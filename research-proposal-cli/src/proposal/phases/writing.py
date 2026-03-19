"""Phase 4: Section-by-section content generation."""

from __future__ import annotations

import re

from rich.console import Console
from rich.panel import Panel

from proposal.config import Domain, Language
from proposal.llm import client as llm
from proposal.llm.prompts import abstract_system_prompt, writing_system_prompt
from proposal.phases.literature import LiteratureCollection
from proposal.phases.requirements import ProposalRequirements
from proposal.ui import spinner

console = Console()

SECTIONS = [
    ("Introduction", "## 1. Introduction"),
    ("Literature Review", "## 2. Literature Review"),
    ("Methodology", "## 3. Methodology"),
    ("Timeline", "## 4. Timeline"),
    ("Significance and Expected Contributions", "## 5. Significance and Expected Contributions"),
    ("References", "## References"),
]


def generate_proposal(
    reqs: ProposalRequirements,
    literature: LiteratureCollection,
    outline: str,
) -> str:
    """Generate the full proposal section by section, then prepend the abstract."""

    console.print("\n[bold blue]Phase 4: Content Generation[/bold blue]")

    generated_sections: dict[str, str] = {}

    for section_name, heading in SECTIONS:
        console.print(f"\n  [bold]{section_name}[/bold]")
        console.print()

        system = writing_system_prompt(
            section_name=section_name,
            domain=reqs.domain,
            language=reqs.language,
            word_count=reqs.word_count,
        )

        # Build context from previously generated sections
        prior_context = ""
        if generated_sections:
            prior_parts = []
            for prev_name, prev_text in generated_sections.items():
                # Include abbreviated context (first 500 chars) to save tokens
                preview = prev_text[:500] + "..." if len(prev_text) > 500 else prev_text
                prior_parts.append(f"### {prev_name} (excerpt)\n{preview}")
            prior_context = "\n\n".join(prior_parts)

        user_msg_parts = [
            f"## Topic: {reqs.topic}",
            f"## Approved Outline\n{outline}",
            f"## Literature Summary\n{literature.summary}",
        ]

        if section_name == "References":
            # For references, give full context of all sections
            full_prior = "\n\n".join(
                f"### {name}\n{text}" for name, text in generated_sections.items()
            )
            user_msg_parts.append(f"## Full Proposal Content\n{full_prior}")
            user_msg_parts.append(
                "Generate the References section with a minimum of 40 references in APA format. "
                "Include all works cited in the proposal sections above, plus additional relevant works. "
                "Ensure ~60% are from the last 5 years."
            )
        else:
            if prior_context:
                user_msg_parts.append(f"## Previously Written Sections\n{prior_context}")
            user_msg_parts.append(
                f"Write the {section_name} section now. "
                "Use flowing prose, not bullet points. "
                "Include citations (Author, Year) throughout."
            )

        user_msg = "\n\n".join(user_msg_parts)

        section_text = llm.generate(
            system_prompt=system,
            user_prompt=user_msg,
            stream=True,
        )
        generated_sections[section_name] = _strip_leading_heading(section_text)

    # Generate abstract last (summarizes everything)
    console.print(f"\n  [bold]Abstract[/bold]")
    console.print()
    full_proposal_preview = "\n\n".join(
        f"## {name}\n{text}" for name, text in generated_sections.items()
        if name != "References"
    )
    abstract_text = llm.generate(
        system_prompt=abstract_system_prompt(reqs.language),
        user_prompt=(
            f"## Topic: {reqs.topic}\n\n"
            f"## Full Proposal\n{full_proposal_preview}\n\n"
            "Write the abstract (150-300 words)."
        ),
        stream=True,
    )

    abstract_text = _strip_leading_heading(abstract_text)

    # Assemble full document
    title_heading = f"# {reqs.topic}"
    parts = [title_heading, "", "## Abstract", "", abstract_text, "", "---", ""]

    for section_name, heading in SECTIONS:
        text = generated_sections.get(section_name, "")
        parts.extend([heading, "", text, "", "---", ""])

    full_document = "\n".join(parts)

    word_count = len(full_document.split())
    console.print(f"\n  [green]Content generation complete.[/green] ({word_count} words)")

    return full_document


def _strip_leading_heading(text: str) -> str:
    """Remove leading H2/H3 heading lines that the LLM may include despite instructions.

    Strips any number of leading blank lines, then any lines starting with ## or ###
    (including numbered variants like '## 2. Literature Review'), until the first
    non-heading, non-blank line.
    """
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if re.match(r"^#{1,3}\s+", stripped):
            i += 1
            continue
        break
    return "\n".join(lines[i:]).strip()
