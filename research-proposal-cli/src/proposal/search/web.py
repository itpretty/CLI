"""Web search via Serper.dev or SerpAPI."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from rich.console import Console

from proposal.config import get_settings

console = Console()


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    date: str = ""


def search(query: str, num_results: int = 10) -> list[SearchResult]:
    """Run a web search and return results. Tries Serper first, then SerpAPI."""
    settings = get_settings()

    if settings.serper_api_key:
        return _serper_search(query, num_results, settings.serper_api_key)
    elif settings.serpapi_key:
        return _serpapi_search(query, num_results, settings.serpapi_key)
    else:
        _warn_no_key()
        return []


_no_key_warned = False


def _warn_no_key() -> None:
    global _no_key_warned
    if not _no_key_warned:
        _no_key_warned = True
        console.print()
        console.print("  [yellow]No web search API key configured. Skipping web search.[/yellow]")
        console.print()


def _serper_search(query: str, num_results: int, api_key: str) -> list[SearchResult]:
    try:
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        console.print(f"[yellow]Web search error: {e}[/yellow]")
        return []

    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            date=item.get("date", ""),
        ))
    return results


def _serpapi_search(query: str, num_results: int, api_key: str) -> list[SearchResult]:
    try:
        resp = httpx.get(
            "https://serpapi.com/search",
            params={"q": query, "num": num_results, "api_key": api_key, "engine": "google"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        console.print(f"[yellow]Web search error: {e}[/yellow]")
        return []

    results = []
    for item in data.get("organic_results", [])[:num_results]:
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            date=item.get("date", ""),
        ))
    return results
