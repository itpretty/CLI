"""Phase 5: Markdown file output."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import questionary
from rich.console import Console

console = Console()


def save_proposal(topic: str, content: str) -> Path:
    """Save the proposal to a Markdown file and return the path."""

    console.print("\n[bold blue]Phase 5: Output[/bold blue]")

    slug = _slugify(topic)
    now = datetime.now()
    timestamp = f"{now.strftime('%Y-%m-%d')}_{now.strftime('%H%M')}"
    default_name = f"proposal_{slug}_{timestamp}.md"

    output_dir = questionary.path(
        "Output directory?",
        default=".",
        only_directories=True,
    ).ask()
    if output_dir is None:
        output_dir = "."

    out_path = Path(output_dir).resolve() / default_name
    out_path.write_text(content, encoding="utf-8")

    console.print(f"  [green]Saved:[/green] {out_path}")
    return out_path


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text)
    return text[:60]
