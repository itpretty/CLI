"""Phase 1: Interactive requirements gathering."""

from __future__ import annotations

from dataclasses import dataclass

import questionary
from rich.console import Console
from rich.panel import Panel

from proposal.config import Domain, Language

console = Console()


@dataclass
class ProposalRequirements:
    topic: str
    domain: Domain
    language: Language
    word_count: int
    institution: str


def gather_requirements(
    topic: str | None = None,
    domain: str | None = None,
    language: str | None = None,
    words: int | None = None,
) -> ProposalRequirements:
    """Interactively collect proposal requirements, using CLI args as defaults."""

    console.print(Panel.fit(
        "[bold]Phase 1: Requirements Gathering[/bold]\n"
        "Let's collect the details for your research proposal.",
        border_style="blue",
    ))

    # Topic
    if not topic:
        topic = questionary.text(
            "What is your research topic or direction?",
            validate=lambda t: len(t.strip()) > 0 or "Please enter a topic.",
        ).ask()
        if topic is None:
            raise SystemExit(0)

    # Domain
    if not domain:
        domain_choice = questionary.select(
            "Which academic domain?",
            choices=[d.value for d in Domain],
        ).ask()
        if domain_choice is None:
            raise SystemExit(0)
        parsed_domain = Domain(domain_choice)
    else:
        parsed_domain = Domain(domain)

    # Language
    if not language:
        lang_choice = questionary.select(
            "Output language?",
            choices=[l.value for l in Language],
        ).ask()
        if lang_choice is None:
            raise SystemExit(0)
        parsed_language = Language(lang_choice)
    else:
        parsed_language = Language(language)

    # Word count
    if not words:
        words_str = questionary.text(
            "Target word count?",
            default="3000",
            validate=lambda v: v.isdigit() and 1000 <= int(v) <= 15000 or "Enter a number between 1000-15000.",
        ).ask()
        if words_str is None:
            raise SystemExit(0)
        word_count = int(words_str)
    else:
        word_count = words

    # Institution (optional)
    institution = questionary.text(
        "Target institution? (optional, press Enter to skip)",
        default="",
    ).ask() or ""

    reqs = ProposalRequirements(
        topic=topic.strip(),
        domain=parsed_domain,
        language=parsed_language,
        word_count=word_count,
        institution=institution.strip(),
    )

    # Display summary
    console.print()
    console.print(Panel(
        f"[bold]Topic:[/bold] {reqs.topic}\n"
        f"[bold]Domain:[/bold] {reqs.domain.value}\n"
        f"[bold]Language:[/bold] {reqs.language.value}\n"
        f"[bold]Word count:[/bold] {reqs.word_count}\n"
        f"[bold]Institution:[/bold] {reqs.institution or '(not specified)'}",
        title="Requirements Summary",
        border_style="green",
    ))

    confirm = questionary.confirm("Proceed with these settings?", default=True).ask()
    if not confirm:
        raise SystemExit(0)

    return reqs
