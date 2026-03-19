"""arXiv search via the arxiv Python package."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console

console = Console()


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    year: int
    paper_id: str
    url: str
    source: str = "arxiv"


def search(query: str, max_results: int = 10) -> list[Paper]:
    """Search arXiv for papers matching the query."""
    try:
        import arxiv
    except ImportError:
        console.print("[yellow]arxiv package not installed. Skipping arXiv search.[/yellow]")
        return []

    try:
        client = arxiv.Client()
        search_query = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        papers = []
        for result in client.results(search_query):
            papers.append(Paper(
                title=result.title,
                authors=[a.name for a in result.authors],
                abstract=result.summary,
                year=result.published.year,
                paper_id=result.entry_id.split("/")[-1],
                url=result.entry_id,
            ))
        return papers

    except Exception as e:
        console.print(f"[yellow]arXiv search error: {e}[/yellow]")
        return []
