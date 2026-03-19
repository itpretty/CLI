"""Phase 6: PDF conversion wrapping the existing md_to_pdf script."""

from __future__ import annotations

import sys
from pathlib import Path

import questionary
from rich.console import Console

from proposal.config import FONTS_DIR, SCRIPTS_DIR

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
        # Import the build_pdf function from our bundled script
        # We need to add the scripts dir to sys.path temporarily
        scripts_dir = str(SCRIPTS_DIR)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from md_to_pdf import build_pdf
        from proposal.ui import spinner

        with spinner("Converting to PDF..."):
            build_pdf(str(md_path), str(pdf_path))
        console.print(f"  [green]PDF saved:[/green] {pdf_path}")
        return pdf_path

    except ImportError:
        console.print("[yellow]PDF conversion script not found. Skipping.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]PDF conversion error: {e}[/red]")
        return None
