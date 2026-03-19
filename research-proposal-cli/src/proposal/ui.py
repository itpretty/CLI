"""Shared UI utilities — spinners, status indicators."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.status import Status

console = Console()


@contextmanager
def spinner(message: str) -> Generator[Status, None, None]:
    """Show an animated spinner with a message while work is in progress.

    Usage:
        with spinner("Generating outline..."):
            result = llm.generate(...)
    """
    with console.status(message, spinner="dots", spinner_style="") as status:
        yield status
