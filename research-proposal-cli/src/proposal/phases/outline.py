"""Phase 3: Outline generation with interactive approval."""

from __future__ import annotations

import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from proposal.config import Domain, Language
from proposal.llm import client as llm
from proposal.llm.prompts import outline_system_prompt
from proposal.phases.literature import LiteratureCollection
from proposal.phases.requirements import ProposalRequirements

console = Console()


def generate_outline(
    reqs: ProposalRequirements,
    literature: LiteratureCollection,
) -> str:
    """Generate proposal outline and get user approval."""

    console.print("\n[bold blue]Phase 3: Outline Generation[/bold blue]")

    system = outline_system_prompt(
        topic=reqs.topic,
        domain=reqs.domain,
        language=reqs.language,
        word_count=reqs.word_count,
        institution=reqs.institution,
    )

    user_msg = (
        f"Generate a detailed research proposal outline for the topic: {reqs.topic}\n\n"
        f"## Literature Summary\n{literature.summary}\n\n"
        "Create the outline with section titles, subsections, and estimated word counts. "
        "Include 3-5 figure suggestions at appropriate locations."
    )

    from proposal.ui import spinner

    while True:
        with spinner("Generating outline..."):
            outline = llm.generate(system_prompt=system, user_prompt=user_msg)

        console.print()
        console.print(Panel(Markdown(outline), title="Proposed Outline", border_style="cyan"))
        console.print()

        action = questionary.select(
            "What would you like to do?",
            choices=["Approve and proceed", "Edit (provide feedback)", "Reject and exit"],
        ).ask()

        if action is None or action == "Reject and exit":
            raise SystemExit(0)

        if action == "Approve and proceed":
            return outline

        # Edit: get feedback and regenerate
        feedback = questionary.text(
            "What changes would you like?",
            validate=lambda t: len(t.strip()) > 0 or "Please provide feedback.",
        ).ask()
        if feedback is None:
            raise SystemExit(0)

        user_msg = (
            f"Revise the following outline based on user feedback.\n\n"
            f"## Current Outline\n{outline}\n\n"
            f"## User Feedback\n{feedback}\n\n"
            f"## Literature Summary\n{literature.summary}\n\n"
            "Generate the revised outline with all sections and word counts."
        )
