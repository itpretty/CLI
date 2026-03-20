"""LLM client that uses the `claude` CLI as its backend.

Invokes `claude -p` (print mode) with the current logged-in session,
so it works with Team/Pro subscriptions without needing API credits.
"""

from __future__ import annotations

import json
import os
import shutil
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

_init_shown = False


_claude_bin: str | None = None


def _find_claude() -> str:
    """Locate the claude CLI binary.

    When running as a PyInstaller bundle, the inherited PATH may be minimal
    (e.g. /usr/bin:/bin), so we also check common installation directories.
    """
    global _claude_bin
    if _claude_bin:
        return _claude_bin

    # 1. Check PATH (works for normal installs and Terminal launches)
    found = shutil.which("claude")
    if found:
        _claude_bin = found
        return found

    # 2. Check common locations for standalone / npm-installed claude
    import pathlib
    home = pathlib.Path.home()
    candidates = [
        home / ".local" / "bin" / "claude",
        home / ".claude" / "local" / "claude",
        home / ".npm-global" / "bin" / "claude",
        pathlib.Path("/usr/local/bin/claude"),
        pathlib.Path("/opt/homebrew/bin/claude"),
    ]
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            _claude_bin = str(p)
            return _claude_bin

    # 3. Ask the shell for the full PATH
    try:
        result = subprocess.run(
            ["/bin/zsh", "-lc", "which claude"],
            capture_output=True, text=True, timeout=5,
        )
        path = result.stdout.strip()
        if path and os.path.isfile(path):
            _claude_bin = path
            return _claude_bin
    except Exception:
        pass

    return ""


def _ensure_cli() -> None:
    """Check that the claude CLI is available and print info on first use."""
    global _init_shown
    if not _find_claude():
        console.print("[red]Error: 'claude' CLI not found on PATH.[/red]")
        console.print("[dim]Install Claude Code: https://docs.anthropic.com/en/docs/claude-code[/dim]")
        raise SystemExit(1)

    if not _init_shown:
        _init_shown = True
        settings = get_settings()
        console.print(
            f"  Using Claude Code CLI, model: [bold]{settings.model}[/bold]"
        )


def _build_env() -> dict[str, str]:
    """Build subprocess environment, stripping ANTHROPIC_API_KEY.

    This forces `claude -p` to use the logged-in session (Team/Pro
    subscription) instead of the API key which may have no credits.
    """
    return {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}


def generate(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int | None = None,
    stream: bool = False,
) -> str:
    """Call the claude CLI and return the assistant's text response."""
    _ensure_cli()
    settings = get_settings()

    prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    env = _build_env()

    if stream:
        return _stream(prompt, settings.model, env)
    return _run(prompt, settings.model, env)


def _run(prompt: str, model: str, env: dict) -> str:
    """Non-streaming: run claude -p and parse JSON result."""
    cmd = [
        _find_claude(),
        "-p",
        "--output-format", "json",
        "--model", model,
        "--no-session-persistence",
        "--append-system-prompt",
        "You are a text generation assistant. Respond ONLY with the requested content. "
        "Do not use any tools. Do not explain or add commentary unless asked.",
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Claude Code CLI timed out after 5 minutes.[/red]")
        return ""

    if result.returncode != 0:
        stderr = result.stderr.strip()
        console.print(f"[red]Claude Code CLI error: {stderr or 'unknown error'}[/red]")
        return ""

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()

    if data.get("is_error"):
        console.print(f"[red]Claude Code error: {data.get('result', 'unknown')}[/red]")
        return ""

    _record_usage(data.get("usage", {}))
    return data.get("result", "")


def _stream(prompt: str, model: str, env: dict) -> str:
    """Streaming: run claude -p with stream-json and print chunks live."""
    cmd = [
        _find_claude(),
        "-p",
        "--verbose",
        "--output-format", "stream-json",
        "--model", model,
        "--no-session-persistence",
        "--append-system-prompt",
        "You are a text generation assistant. Respond ONLY with the requested content. "
        "Do not use any tools. Do not explain or add commentary unless asked.",
        prompt,
    ]

    collected = []

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except OSError as e:
        console.print(f"[red]Failed to start claude CLI: {e}[/red]")
        return ""

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


def _record_usage(u: dict) -> None:
    input_tok = (
        u.get("input_tokens", 0)
        + u.get("cache_read_input_tokens", 0)
        + u.get("cache_creation_input_tokens", 0)
    )
    output_tok = u.get("output_tokens", 0)
    usage.record(input_tok, output_tok)
