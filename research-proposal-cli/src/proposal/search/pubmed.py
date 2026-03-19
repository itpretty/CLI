"""PubMed search via pymed."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console

from proposal.search.arxiv_search import Paper

console = Console()


def search(query: str, max_results: int = 10) -> list[Paper]:
    """Search PubMed for papers matching the query."""
    try:
        from pymed import PubMed
    except ImportError:
        console.print("[yellow]pymed package not installed. Skipping PubMed search.[/yellow]")
        return []

    try:
        pubmed = PubMed(tool="ResearchProposalCLI", email="user@example.com")
        results = pubmed.query(query, max_results=max_results)

        papers = []
        for article in results:
            title = getattr(article, "title", "") or ""
            abstract = getattr(article, "abstract", "") or ""
            pubmed_id = getattr(article, "pubmed_id", "") or ""
            pub_date = getattr(article, "publication_date", None)

            authors_raw = getattr(article, "authors", []) or []
            authors = []
            for a in authors_raw:
                if isinstance(a, dict):
                    name = f"{a.get('firstname', '')} {a.get('lastname', '')}".strip()
                    if name:
                        authors.append(name)
                elif isinstance(a, str):
                    authors.append(a)

            year = 0
            if pub_date:
                if hasattr(pub_date, "year"):
                    year = pub_date.year
                else:
                    try:
                        year = int(str(pub_date)[:4])
                    except (ValueError, TypeError):
                        pass

            # Clean pubmed_id (may contain newlines or multiple IDs)
            clean_id = pubmed_id.strip().split("\n")[0].strip()

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                paper_id=clean_id,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{clean_id}/" if clean_id else "",
                source="pubmed",
            ))
        return papers

    except Exception as e:
        console.print(f"[yellow]PubMed search error: {e}[/yellow]")
        return []
