import os

from dotenv import load_dotenv
from loguru import logger

from . import scrape

# Check the environmental variables are configured.
load_dotenv()
google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
google_search_id = os.getenv("GOOGLE_SEARCH_ID")

if not google_search_api_key or not google_search_id:
    message = (
        "GOOGLE_SEARCH_API_KEY and/or GOOGLE_SEARCH_ID environmental variable not set."
    )
    logger.error(message)
    raise ValueError(message)


def google(
    query: str,
    max_results: int = 10,
    page_start: int = 1,
    sort_by: Optional[str] = None,
    should_scrape_links: bool = False,
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

    # # Scrape the search result links to get website body.
    # if should_scrape_links:
    #     _search_results = []
    #     for search_result in search_results:
    #         _search_result = search_result
    #         if data := scrape.data_from_search_result(search_result):
    #             _search_result = _search_result | {"body": body}
    #         _search_results.append(_search_result)
    #     search_results = _search_results

    return search_results
