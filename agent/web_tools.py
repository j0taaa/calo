from typing import List, Dict, Any

import logging

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

logger = logging.getLogger(__name__)


def search_web(query: str, num_results: int = 5, region: str = "us-en") -> List[Dict[str, Any]]:
    """Search the web and return a list of results with title, url, and snippet.
    Uses DuckDuckGo (no API key required).
    """
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            try:
                search_iter = ddgs.text(
                    query,
                    region=region,
                    safesearch="moderate",
                    max_results=num_results,
                    backend="bing",
                )
            except TypeError:
                # Older versions of duckduckgo_search do not support the backend parameter
                search_iter = ddgs.text(
                    query,
                    region=region,
                    safesearch="moderate",
                    max_results=num_results,
                )
            for r in search_iter:
                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body"),
                    }
                )
    except DuckDuckGoSearchException as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
    return results
