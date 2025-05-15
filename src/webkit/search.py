import os
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from . import scrape

load_dotenv()


def brave(
    query: str, max_results: int = 20, api_key: Optional[str] = None
) -> list[dict]:
    """https://api-dashboard.search.brave.com/app/documentation/"""
    api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
    if api_key is None:
        message = "api_key must be passed or set in BRAVE_SEARCH_API_KEY"
        logger.error(message)
        return []

    url = f"https://api.search.brave.com/res/v1/web/search"
    params = {"q": query, "count": max_results}
    headers = {"X-Subscription-Token": api_key}

    response, error = scrape.get_response(url, params=params, headers=headers)
    if error:
        logger.debug(f"Failed to get response: {error = }")
        return []

    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"JSON decoding failed: {e}")
        return []

    raw_search_results = data.get("web", {}).get("results", [])
    search_results = []

    for raw_search_result in raw_search_results:
        title = raw_search_result.get("title", "")
        url = raw_search_result.get("url", "")
        description = raw_search_result.get("description", "")
        extra_snippets = " ".join(raw_search_result.get("extra_snippets", []))
        search_result = {
            "title": title,
            "url": url,
            "description": f"{description} {extra_snippets}",
        }
        logger.debug(f"{search_result = }")
        search_results.append(search_result)
    logger.debug(f"Total search results retrieved: {len(search_results)}")
    return search_results


# google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
# google_search_id = os.getenv("GOOGLE_SEARCH_ID")

# if not google_search_api_key or not google_search_id:
#     message = (
#         "GOOGLE_SEARCH_API_KEY and/or GOOGLE_SEARCH_ID environmental variable not set."
#     )
#     logger.error(message)
#     raise ValueError(message)

# brave_search_api_key = os.getenv("BRAVE_SEARCH_API_KEY")


def google(
    query: str,
    max_results: int = 10,
    page_start: int = 1,
    sort_by: Optional[str] = None,
) -> list[dict]:
    """https://developers.google.com/custom-search/v1/overview"""

    search_results = []

    # Construct search request.
    url = f"https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "cx": google_search_id,
        "key": google_search_api_key,
        "q": query,
        "num": max_results,
        "start": page_start,
    }
    if sort_by:
        params["sort"] = sort_by
    response, error = scrape.get_response(url, params=params)
    logger.debug(f"{response = } {error = }".encode("UTF-8"))

    # Format search results keys.
    try:
        data = response.json()
        items = data.get("items", [])
        keys = ("title", "link", "snippet")
        for item in items:
            search_result = {k: v for k, v in item.items() if k in keys}
            search_result["href"] = search_result.pop("link")
            search_result["body"] = ""
            search_results.append(search_result)
    except Exception as e:
        return search_results
    logger.debug(f"{search_results = }".encode("UTF-8"))

    return search_results
