"""Automated quality checks for research proposals."""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def validate(md_path: str | Path) -> bool:
    """Run quality checks on a Markdown proposal file. Returns True if all critical checks pass."""

    text = Path(md_path).read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []

    # Word count
    words = text.split()
    word_count = len(words)
    results.append(("Word count (2000-4000)", 2000 <= word_count <= 4000, f"{word_count} words"))

    # Required sections
    required = ["Abstract", "Introduction", "Literature Review", "Methodology", "Timeline", "Significance", "References"]
    for section in required:
        found = bool(re.search(rf"^#+\s+.*{re.escape(section)}", text, re.MULTILINE | re.IGNORECASE))
        results.append((f"Section: {section}", found, "present" if found else "MISSING"))

    # Reference count
    ref_section = _extract_section(text, "References")
    ref_lines = [l for l in ref_section.split("\n") if l.strip() and not l.startswith("#")]
    ref_count = len(ref_lines)
    results.append(("References >= 40", ref_count >= 40, f"{ref_count} references"))

    # Reference recency (60% from last 5 years)
    years = re.findall(r"\((\d{4})\)", ref_section)
    if years:
        recent = sum(1 for y in years if int(y) >= 2021)
        pct = recent / len(years) * 100
        results.append(("References recency (>=60% last 5yr)", pct >= 60, f"{pct:.0f}%"))
    else:
        results.append(("References recency", False, "no years found"))

    # Abbreviation first-use check (simplified)
    abbrevs = re.findall(r"\b([A-Z]{2,6})\b", text)
    abbrev_set = set(abbrevs)
    defined = set()
    for a in abbrev_set:
        if re.search(rf"\([^)]*{re.escape(a)}[^)]*\)", text):
            defined.add(a)
    undefined = abbrev_set - defined - {"PhD", "AI", "ML", "NLP", "DNA", "RNA", "MRI", "CT", "UK", "US", "EU"}
    results.append(("Abbreviations defined", len(undefined) <= 3, f"{len(undefined)} possibly undefined"))

    # Heading structure
    h2_count = len(re.findall(r"^## ", text, re.MULTILINE))
    results.append(("Heading count (>=5 H2)", h2_count >= 5, f"{h2_count} H2 headings"))

    # Citation format (APA parenthetical)
    citations = re.findall(r"\([A-Z][a-z]+ (?:et al\., )?\d{4}\)", text)
    results.append(("In-text citations present", len(citations) >= 10, f"{len(citations)} found"))

    # Figure suggestions
    figures = re.findall(r"\[Figure \d+ Suggestion\]", text, re.IGNORECASE)
    results.append(("Figure suggestions (3-5)", 3 <= len(figures) <= 5, f"{len(figures)} found"))

    # Display results
    table = Table(title="Quality Check Results", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Detail")

    all_pass = True
    for name, passed, detail in results:
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        if not passed:
            all_pass = False
        table.add_row(name, status, detail)

    console.print()
    console.print(table)

    if all_pass:
        console.print("\n[green bold]All checks passed.[/green bold]")
    else:
        console.print("\n[yellow]Some checks did not pass. Review the results above.[/yellow]")

    return all_pass


def _extract_section(text: str, section_name: str) -> str:
    """Extract text from a named section to the next section or end of file."""
    pattern = rf"^#+\s+.*{re.escape(section_name)}.*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    # Find next heading at same or higher level
    level = len(match.group(0).split()[0])  # count #'s
    next_heading = re.search(rf"^#{{1,{level}}}\s+", text[start:], re.MULTILINE)
    if next_heading:
        return text[start:start + next_heading.start()]
    return text[start:]
