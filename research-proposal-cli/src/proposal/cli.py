"""CLI entry point using Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="proposal",
    help="Generate academic research proposals by AI",
    invoke_without_command=True,
)
console = Console()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Generate academic research proposals by AI."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            generate,
            topic=None,
            domain=None,
            language=None,
            words=None,
            skip_pdf=False,
            model=None,
        )


PHASES = [
    ("1", "Requirements", "Collect topic, domain, language, word count"),
    ("2", "Literature",    "Search arXiv, PubMed, and web for papers"),
    ("3", "Outline",       "Generate outline for user approval"),
    ("4", "Writing",       "Section-by-section content generation"),
    ("5", "Output",        "Save Markdown file"),
    ("6", "PDF",           "Convert to professional PDF"),
]


def _banner(skip_pdf: bool = False) -> None:
    from rich.table import Table
    from rich.text import Text

    try:
        import pyfiglet
        logo = pyfiglet.figlet_format("VibeSci", font="slant")
        console.print(Text(logo, style="bold blue"), end="")
    except ImportError:
        console.print("[bold blue]VibeSci[/bold blue]")

    console.print("[dim italic]VibeSci - Research Proposal Generator by www.opensci.io[/dim italic]")
    console.print()

    from rich.box import SIMPLE_HEAVY

    table = Table(box=SIMPLE_HEAVY, show_edge=False, padding=(0, 2))
    table.add_column("Phase", style="bold cyan", justify="center")
    table.add_column("Name", style="bold")
    table.add_column("Description", style="dim")
    for num, name, desc in PHASES:
        if num == "6" and skip_pdf:
            table.add_row(num, name, f"{desc} [dim italic](skipped)[/dim italic]")
        else:
            table.add_row(num, name, desc)

    console.print(Panel(table, title="Phases", border_style="dim", expand=False))
    console.print()


@app.command()
def generate(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Research topic"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="STEM / Humanities / Social Sciences"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="English / Chinese"),
    words: Optional[int] = typer.Option(None, "--words", "-w", help="Target word count"),
    skip_pdf: bool = typer.Option(False, "--skip-pdf", help="Skip PDF conversion"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Claude model alias: sonnet, opus, haiku"),
) -> None:
    """Run the full 6-phase proposal generation pipeline."""
    import time

    from proposal.config import get_settings
    from proposal.llm.client import usage
    from proposal.phases import literature, outline, output, pdf, requirements, writing

    if model:
        get_settings().model = model

    _banner(skip_pdf=skip_pdf)
    start_time = time.monotonic()

    # Phase 1: Requirements
    reqs = requirements.gather_requirements(
        topic=topic,
        domain=domain,
        language=language,
        words=words,
    )

    # Phase 2: Literature
    lit = literature.collect_literature(reqs.topic, reqs.domain)

    # Phase 3: Outline
    approved_outline = outline.generate_outline(reqs, lit)

    # Phase 4: Writing
    proposal_text = writing.generate_proposal(reqs, lit, approved_outline)

    # Phase 5: Output
    md_path = output.save_proposal(reqs.topic, proposal_text)

    # Phase 6: PDF
    if not skip_pdf:
        pdf.convert_to_pdf(md_path)

    # Summary
    elapsed = time.monotonic() - start_time
    minutes = elapsed / 60
    console.print()
    console.print(Panel(
        f"[green bold]Proposal generation complete![/green bold]\n\n"
        f"[bold]Time:[/bold] {minutes:.1f} min\n"
        f"[bold]Token usage:[/bold] {usage.summary()}",
        border_style="green",
    ))


@app.command()
def pdf(
    input_md: Path = typer.Argument(..., help="Input Markdown file", exists=True),
    output_pdf: Optional[Path] = typer.Argument(None, help="Output PDF path"),
) -> None:
    """Convert a Markdown proposal to PDF."""
    from proposal.pdf_converter import build_pdf

    out = str(output_pdf) if output_pdf else None
    build_pdf(str(input_md), out)


@app.command()
def validate(
    input_md: Path = typer.Argument(..., help="Input Markdown file", exists=True),
) -> None:
    """Run quality checks on an existing proposal."""
    from proposal.validators.quality import validate as run_validate

    _banner()
    passed = run_validate(input_md)
    raise typer.Exit(0 if passed else 1)


if __name__ == "__main__":
    app()
