"""AI agent CLI detection and adapter layer.

Detects available AI coding CLIs on the user's machine and provides
a unified interface for invoking them in non-interactive mode.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

from rich.console import Console

console = Console()


@dataclass
class AgentInfo:
    """Metadata for a supported AI agent CLI."""

    name: str
    binary: str
    description: str
    tier: str

    # Resolved path (filled by detect)
    path: str = ""


# Registry of supported agents, ordered by tier/priority
SUPPORTED_AGENTS: list[AgentInfo] = [
    # Tier 1
    AgentInfo(
        name="Claude Code",
        binary="claude",
        description="Anthropic's agentic CLI for Claude",
        tier="Tier 1",
    ),
    AgentInfo(
        name="GitHub Copilot CLI",
        binary="copilot",
        description="GitHub Copilot for the command line",
        tier="Tier 1",
    ),
    AgentInfo(
        name="Cursor CLI",
        binary="cursor-agent",
        description="Cursor AI-first code editor CLI",
        tier="Tier 1",
    ),
    # Tier 2
    AgentInfo(
        name="Aider",
        binary="aider",
        description="Open-source AI pair programming CLI",
        tier="Tier 2",
    ),
    AgentInfo(
        name="Open Interpreter",
        binary="interpreter",
        description="LLM-powered code execution CLI",
        tier="Tier 2",
    ),
    AgentInfo(
        name="Codex CLI",
        binary="codex",
        description="OpenAI's coding agent for the terminal",
        tier="Tier 2",
    ),
    AgentInfo(
        name="Cline",
        binary="cline",
        description="Agentic CLI (formerly Claude Dev)",
        tier="Tier 2",
    ),
]


def _find_binary(name: str) -> str:
    """Locate a binary, checking PATH and common install locations."""
    found = shutil.which(name)
    if found:
        return found

    import pathlib

    home = pathlib.Path.home()
    candidates = [
        home / ".local" / "bin" / name,
        home / ".npm-global" / "bin" / name,
        pathlib.Path("/usr/local/bin") / name,
        pathlib.Path("/opt/homebrew/bin") / name,
    ]
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    # Ask the shell
    try:
        result = subprocess.run(
            ["/bin/zsh", "-lc", f"which {name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        path = result.stdout.strip()
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass

    return ""


def detect_agents() -> list[AgentInfo]:
    """Scan the system for available AI agent CLIs."""
    available = []
    for agent in SUPPORTED_AGENTS:
        path = _find_binary(agent.binary)
        if path:
            agent.path = path
            available.append(agent)
    return available


def select_agent(available: list[AgentInfo]) -> AgentInfo:
    """Let the user choose which AI agent to use.

    If only one is found, auto-selects it.
    """
    import questionary

    if len(available) == 1:
        agent = available[0]
        console.print(
            f"  AI Agent: [bold]{agent.name}[/bold] [dim]({agent.path})[/dim]"
        )
        return agent

    choices = []
    for agent in available:
        label = f"{agent.name} — {agent.description}"
        choices.append(questionary.Choice(title=label, value=agent))

    selected = questionary.select(
        "Select AI agent on your computer:",
        choices=choices,
    ).ask()

    if selected is None:
        raise SystemExit(0)

    console.print(
        f"  AI Agent: [bold]{selected.name}[/bold] [dim]({selected.path})[/dim]"
    )
    return selected
