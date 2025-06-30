import os
from typing import Optional, Any, List

import httpx
from loguru import logger


async def get_brave_results_async(
    query: str, max_results: int = 20, api_key: Optional[str] = None
) -> List[dict[str, Any]]:
    """Fetch raw Brave Search results from the API."""
    api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        logger.error("API key must be passed or set in BRAVE_SEARCH_API_KEY")
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query, "count": max_results}
    headers = {"X-Subscription-Token": api_key}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("web", {}).get("results", [])
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Request failed: {e}")
        except ValueError as e:
            logger.error(f"JSON decoding failed: {e}")
    return []


def format_brave_result(raw_result: dict[str, Any]) -> dict[str, str]:
    """Format a single Brave search result into a structured dict."""
    title = raw_result.get("title", "")
    url = raw_result.get("url", "")
    description = raw_result.get("description", "")
    extra_snippets = " ".join(raw_result.get("extra_snippets", []))
    return {
        "title": title,
        "href": url,
        "snippet": f"{description} {extra_snippets}".strip(),
    }
