"""System prompt assembly from template files."""

from __future__ import annotations

from proposal.config import TEMPLATES_DIR, Domain, Language


def _read_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def outline_system_prompt(
    topic: str,
    domain: Domain,
    language: Language,
    word_count: int,
    institution: str = "",
) -> str:
    structure_guide = _read_template("STRUCTURE_GUIDE.md")
    domain_templates = _read_template("DOMAIN_TEMPLATES.md")
    scaffold = _read_template(
        "proposal_scaffold_zh.md" if language == Language.CHINESE else "proposal_scaffold_en.md"
    )

    parts = [
        "You are an expert academic advisor who creates research proposal outlines "
        "for PhD applications. You follow Nature Reviews-style academic writing conventions.",
        "",
        f"## Task: Generate a proposal outline",
        f"- Topic: {topic}",
        f"- Domain: {domain.value}",
        f"- Language: {language.value}",
        f"- Target word count: {word_count}",
    ]
    if institution:
        parts.append(f"- Target institution: {institution}")

    parts.extend([
        "",
        "## Structure Guide",
        structure_guide,
        "",
        "## Domain Templates",
        domain_templates,
        "",
        "## Scaffold Reference",
        scaffold,
        "",
        "## Instructions",
        "Generate a detailed outline with section titles and estimated word counts.",
        "Use the scaffold as a structural reference but adapt to the specific topic.",
        "Include 3-5 figure suggestions at appropriate locations.",
        "Do NOT include appendix sections.",
        "Output the outline in Markdown format.",
    ])
    return "\n".join(parts)


def writing_system_prompt(
    section_name: str,
    domain: Domain,
    language: Language,
    word_count: int,
) -> str:
    style_guide = _read_template("WRITING_STYLE_GUIDE.md")
    quality_checklist = _read_template("QUALITY_CHECKLIST.md")

    parts = [
        "You are an expert academic writer producing a research proposal section "
        "for a PhD application. Follow Nature Reviews-style conventions.",
        "",
        f"## Current section: {section_name}",
        f"- Domain: {domain.value}",
        f"- Language: {language.value}",
        f"- Total proposal word count target: {word_count}",
        "",
        "## Writing Style Guide",
        style_guide,
        "",
        "## Quality Standards (excerpt)",
        "- Write in flowing prose, NOT bullet points",
        "- Use hedging language (may, might, suggests, indicates)",
        "- Maintain formal academic register",
        "- Support claims with citations (Author, Year)",
        "- Ensure smooth transitions between paragraphs",
        "- Include figure suggestions where appropriate",
        "",
        "## Instructions",
        "Write ONLY the requested section. Output raw Markdown.",
        "Do NOT repeat the section heading — it will be added by the system.",
        "Integrate citations naturally into the text.",
    ]
    return "\n".join(parts)


def literature_system_prompt(topic: str, domain: Domain) -> str:
    lit_workflow = _read_template("LITERATURE_WORKFLOW.md")

    return "\n".join([
        "You are an expert research literature analyst. Your task is to analyze "
        "and categorize research literature for a PhD proposal.",
        "",
        f"## Research topic: {topic}",
        f"## Domain: {domain.value}",
        "",
        "## Literature Workflow Reference",
        lit_workflow,
        "",
        "## Instructions",
        "Analyze the provided search results and literature.",
        "Categorize each paper into one of 5 categories:",
        "1. Background/Context",
        "2. State-of-the-Art",
        "3. Gap-Identifying",
        "4. Methodology",
        "5. Related Work",
        "",
        "For each paper provide: authors, year, title, category, and a 1-2 sentence summary.",
        "Identify the most important findings and research gaps.",
        "Output a structured Markdown summary.",
    ])


def search_query_prompt(topic: str, domain: Domain) -> str:
    return "\n".join([
        "Generate 5 search queries for academic literature on the following topic.",
        "Each query should target a different aspect:",
        "1. Recent reviews and state-of-the-art",
        "2. Methodology and techniques",
        "3. Research gaps and limitations",
        "4. Trends and future directions",
        "5. Foundational/seminal works",
        "",
        f"Topic: {topic}",
        f"Domain: {domain.value}",
        "",
        "Output ONLY the 5 queries, one per line, no numbering or explanation.",
    ])


def abstract_system_prompt(language: Language) -> str:
    return "\n".join([
        "You are an expert academic writer. Write an abstract (150-300 words) "
        "that summarizes the entire research proposal.",
        "",
        f"Language: {language.value}",
        "",
        "The abstract must include:",
        "- Background/context (1-2 sentences)",
        "- Research problem (1-2 sentences)",
        "- Objectives (1-2 sentences)",
        "- Methodology overview (2-3 sentences)",
        "- Expected significance (1-2 sentences)",
        "",
        "Do NOT include citations in the abstract.",
        "Use appropriate hedging language.",
        "Output raw text only — no heading.",
    ])
