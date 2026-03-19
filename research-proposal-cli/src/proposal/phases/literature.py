"""Phase 2: Literature search and organization."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from proposal.config import Domain
from proposal.llm import client as llm
from proposal.llm.prompts import literature_system_prompt, search_query_prompt
from proposal.search import arxiv_search, pubmed, web
from proposal.search.arxiv_search import Paper
from proposal.search.web import SearchResult

console = Console()


@dataclass
class LiteratureCollection:
    papers: list[Paper] = field(default_factory=list)
    web_results: list[SearchResult] = field(default_factory=list)
    summary: str = ""


def collect_literature(topic: str, domain: Domain) -> LiteratureCollection:
    """Search multiple sources and organize literature by category."""

    console.print("\n[bold blue]Phase 2: Literature Collection[/bold blue]")

    from proposal.ui import spinner

    # Generate search queries via LLM
    with spinner("Generating search queries..."):
        queries_text = llm.generate(
            system_prompt="You generate academic search queries. Output only the queries, one per line.",
            user_prompt=search_query_prompt(topic, domain),
            max_tokens=500,
        )
    queries = [q.strip() for q in queries_text.strip().split("\n") if q.strip()]
    if not queries:
        queries = [topic]  # fallback

    collection = LiteratureCollection()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Web search
        task = progress.add_task("Searching the web...", total=len(queries))
        for q in queries[:3]:
            results = web.search(q, num_results=5)
            collection.web_results.extend(results)
            progress.advance(task)

        # arXiv (STEM and Social Sciences)
        if domain in (Domain.STEM, Domain.SOCIAL_SCIENCES):
            task = progress.add_task("Searching arXiv...", total=len(queries))
            for q in queries[:3]:
                papers = arxiv_search.search(q, max_results=5)
                collection.papers.extend(papers)
                progress.advance(task)

        # PubMed (STEM and Social Sciences)
        if domain in (Domain.STEM, Domain.SOCIAL_SCIENCES):
            task = progress.add_task("Searching PubMed...", total=len(queries))
            for q in queries[:3]:
                papers = pubmed.search(q, max_results=5)
                collection.papers.extend(papers)
                progress.advance(task)

    # Deduplicate papers by title (case-insensitive)
    seen_titles: set[str] = set()
    unique_papers: list[Paper] = []
    for p in collection.papers:
        key = p.title.lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            unique_papers.append(p)
    collection.papers = unique_papers

    console.print(
        f"  Found [bold]{len(collection.papers)}[/bold] papers and "
        f"[bold]{len(collection.web_results)}[/bold] web results."
    )

    # Use LLM to summarize and categorize
    with spinner("Analyzing and categorizing literature..."):
        lit_context = _format_literature_for_llm(collection)
        collection.summary = llm.generate(
            system_prompt=literature_system_prompt(topic, domain),
            user_prompt=f"Here are the search results to analyze:\n\n{lit_context}",
            max_tokens=4096,
        )

    console.print("  [green]Literature collection complete.[/green]")
    return collection


def _format_literature_for_llm(collection: LiteratureCollection) -> str:
    """Format collected literature into a string for LLM analysis."""
    parts = []

    if collection.papers:
        parts.append("## Academic Papers\n")
        for i, p in enumerate(collection.papers[:30], 1):
            authors_str = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors_str += " et al."
            abstract_preview = p.abstract[:300] + "..." if len(p.abstract) > 300 else p.abstract
            parts.append(
                f"{i}. **{p.title}** ({p.year})\n"
                f"   Authors: {authors_str}\n"
                f"   Source: {p.source} | {p.url}\n"
                f"   Abstract: {abstract_preview}\n"
            )

    if collection.web_results:
        parts.append("\n## Web Search Results\n")
        for i, r in enumerate(collection.web_results[:15], 1):
            parts.append(
                f"{i}. **{r.title}**\n"
                f"   URL: {r.url}\n"
                f"   Snippet: {r.snippet}\n"
            )

    return "\n".join(parts)
