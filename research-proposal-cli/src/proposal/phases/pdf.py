"""Phase 6: PDF conversion wrapping the existing md_to_pdf script."""

from __future__ import annotations

from pathlib import Path

import questionary
from rich.console import Console

console = Console()


def convert_to_pdf(md_path: Path) -> Path | None:
    """Optionally convert the Markdown proposal to PDF."""

    console.print("\n[bold blue]Phase 6: PDF Conversion[/bold blue]")

    convert = questionary.confirm("Convert to PDF?", default=True).ask()
    if not convert:
        console.print("  Skipping PDF conversion.")
        return None

    pdf_path = md_path.with_suffix(".pdf")

    try:
        from proposal.pdf_converter import build_pdf
        from proposal.ui import spinner

        with spinner("Converting to PDF..."):
            build_pdf(str(md_path), str(pdf_path))
        console.print(f"  [green]PDF saved:[/green] {pdf_path}")
        return pdf_path

    except ImportError:
        console.print("[yellow]PDF conversion module not found. Skipping.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]PDF conversion error: {e}[/red]")
        return None
