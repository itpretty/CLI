"""LLM client that dispatches to the selected AI agent CLI.

Supports Claude Code, GitHub Copilot CLI, Cursor CLI, Aider,
Open Interpreter, Codex CLI, and Cline — all via subprocess.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass

from rich.console import Console

from proposal.config import get_settings

console = Console()


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def record(self, inp: int, out: int) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.calls += 1

    def summary(self) -> str:
        return (
            f"API calls: {self.calls} | "
            f"Input: {self.input_tokens:,} | "
            f"Output: {self.output_tokens:,} | "
            f"Total: {self.total:,} tokens"
        )


# Global token tracker for the session
usage = TokenUsage()

_SYSTEM_SUFFIX = (
    "You are a text generation assistant. Respond ONLY with the requested content. "
    "Do not use any tools. Do not explain or add commentary unless asked."
)


def _build_env() -> dict[str, str]:
    """Build subprocess environment, stripping ANTHROPIC_API_KEY."""
    return {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}


# ── Agent-specific command builders ──────────────────────────────────────


def _cmd_claude(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    fmt = "stream-json" if stream else "json"
    cmd = [
        path, "-p",
        "--output-format", fmt,
        "--model", model,
        "--no-session-persistence",
        "--append-system-prompt", _SYSTEM_SUFFIX,
        prompt,
    ]
    if stream:
        cmd.insert(2, "--verbose")
    return cmd


def _cmd_copilot(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    return [path, "-p", f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}"]


def _cmd_cursor(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    cmd = [path, "-p", f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}"]
    if model:
        cmd.extend(["-m", model])
    return cmd


def _cmd_aider(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    return [
        path,
        "--chat-mode", "ask",
        "--no-auto-commits",
        "--yes",
        "--no-stream",
        "--message", f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}",
    ]


def _cmd_interpreter(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    return [path, "-y", f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}"]


def _cmd_codex(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    cmd = [
        path, "exec",
        "--approval-mode", "never",
        f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}",
    ]
    if model:
        cmd.extend(["-m", model])
    return cmd


def _cmd_cline(path: str, prompt: str, model: str, stream: bool) -> list[str]:
    return [path, "-y", f"{_SYSTEM_SUFFIX}\n\n---\n\n{prompt}"]


_CMD_BUILDERS = {
    "claude": _cmd_claude,
    "copilot": _cmd_copilot,
    "cursor-agent": _cmd_cursor,
    "aider": _cmd_aider,
    "interpreter": _cmd_interpreter,
    "codex": _cmd_codex,
    "cline": _cmd_cline,
}


# ── Response parsers ─────────────────────────────────────────────────────


def _parse_claude_json(stdout: str) -> str:
    """Parse Claude Code JSON response."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout.strip()
    if data.get("is_error"):
        console.print(f"[red]Claude Code error: {data.get('result', 'unknown')}[/red]")
        return ""
    _record_usage(data.get("usage", {}))
    return data.get("result", "")


def _parse_plain(stdout: str) -> str:
    """Generic parser — just return stripped text."""
    return stdout.strip()


_PARSERS = {
    "claude": _parse_claude_json,
    "copilot": _parse_plain,
    "cursor-agent": _parse_plain,
    "aider": _parse_plain,
    "interpreter": _parse_plain,
    "codex": _parse_plain,
    "cline": _parse_plain,
}


# ── Stream parsers ───────────────────────────────────────────────────────


def _stream_claude(proc: subprocess.Popen) -> str:
    """Parse Claude Code stream-json output."""
    collected = []
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type")
        if etype == "assistant" and "message" in event:
            for block in event["message"].get("content", []):
                if block.get("type") == "text":
                    text = block["text"]
                    console.print(text, end="", highlight=False)
                    collected.append(text)
        elif etype == "result":
            result_text = event.get("result", "")
            if result_text and not collected:
                collected.append(result_text)
            _record_usage(event.get("usage", {}))
    proc.wait()
    console.print()
    return "".join(collected)


def _stream_plain(proc: subprocess.Popen) -> str:
    """Generic streaming — print lines as they arrive."""
    collected = []
    for line in proc.stdout:
        console.print(line, end="", highlight=False)
        collected.append(line)
    proc.wait()
    if collected and not collected[-1].endswith("\n"):
        console.print()
    return "".join(collected).strip()


_STREAMERS = {
    "claude": _stream_claude,
    "copilot": _stream_plain,
    "cursor-agent": _stream_plain,
    "aider": _stream_plain,
    "interpreter": _stream_plain,
    "codex": _stream_plain,
    "cline": _stream_plain,
}


# ── Public API ───────────────────────────────────────────────────────────


def generate(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int | None = None,
    stream: bool = False,
) -> str:
    """Call the selected AI agent CLI and return the response text."""
    settings = get_settings()
    agent = settings.agent
    path = settings.agent_path

    if not path:
        console.print(f"[red]Error: No AI agent configured.[/red]")
        raise SystemExit(1)

    prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

    builder = _CMD_BUILDERS.get(agent)
    if not builder:
        console.print(f"[red]Error: Unsupported agent '{agent}'[/red]")
        raise SystemExit(1)

    cmd = builder(path, prompt, settings.model, stream)
    env = _build_env()

    if stream:
        return _run_stream(cmd, env, agent)
    return _run_sync(cmd, env, agent)


def _run_sync(cmd: list[str], env: dict, agent: str) -> str:
    """Non-streaming execution."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Agent CLI timed out after 5 minutes.[/red]")
        return ""

    if result.returncode != 0:
        stderr = result.stderr.strip()
        console.print(f"[red]Agent CLI error: {stderr or 'unknown error'}[/red]")
        return ""

    parser = _PARSERS.get(agent, _parse_plain)
    return parser(result.stdout)


def _run_stream(cmd: list[str], env: dict, agent: str) -> str:
    """Streaming execution."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except OSError as e:
        console.print(f"[red]Failed to start agent CLI: {e}[/red]")
        return ""

    streamer = _STREAMERS.get(agent, _stream_plain)
    return streamer(proc)


def _record_usage(u: dict) -> None:
    input_tok = (
        u.get("input_tokens", 0)
        + u.get("cache_read_input_tokens", 0)
        + u.get("cache_creation_input_tokens", 0)
    )
    output_tok = u.get("output_tokens", 0)
    usage.record(input_tok, output_tok)
