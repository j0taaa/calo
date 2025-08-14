from typing import List, Dict, Any

from duckduckgo_search import DDGS


def search_web(query: str, num_results: int = 5, region: str = "us-en") -> List[Dict[str, Any]]:
    """Search the web and return a list of results with title, url, and snippet.
    Uses DuckDuckGo (no API key required).
    """
    results: List[Dict[str, Any]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, region=region, safesearch="moderate", max_results=num_results):
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body"),
            })
    return results