import os

from dotenv import load_dotenv
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import (
    DuckDuckGoSearchException,
    RatelimitException,
    TimeoutException,
)
from loguru import logger

from . import scrape

load_dotenv()
google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
google_search_id = os.getenv("GOOGLE_SEARCH_ID")


def duckduckgo(query: str, max_results: int = 10) -> list[dict]:
    logger.debug(f"{query = } {max_results = }")
    try:
        results = DDGS().text(query, safesearch="off", max_results=max_results)
        logger.debug(f"{len(results)} results found.")
    except DuckDuckGoSearchException as e:
        logger.error(f"DuckDuckGoSearchException: {e}")
        results = []
    except RatelimitException as e:
        logger.error(f"RatelimitException: {e}")
        results = []
    except TimeoutException as e:
        logger.error(f"TimeoutException: {e}")
        results = []
    except Exception as e:
        logger.error(f"Unknown error: {e}")
        results = []
    return results


def google(query: str, max_results: int = 10) -> list[dict]:
    """https://developers.google.com/custom-search/v1/overview"""
    search_results = []
    if not google_search_api_key or not google_search_id:
        logg.error(
            "GOOGLE_SEARCH_API_KEY and/or GOOGLE_SEARCH_ID environmental variable not set."
        )
        return search_results
    url = f"https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "cx": google_search_id,
        "key": google_search_api_key,
        "q": query,
        # "sort": "date",
        "num": max_results,
        "start": 1,
    }
    response, error = scrape.get_response(url, params=params)
    if response:
        logger.info(f"{response = }".encode("UTF-8"))
        try:
            data = response.json()
            items = data.get("items", [])
            keys = ("title", "link", "snippet")
            for item in items:
                search_result = {k: v for k, v in item.items() if k in keys}
                search_result["body"] = search_result.pop("snippet")
                search_result["href"] = search_result.pop("link")
                search_results.append(search_result)
        except Exception as e:
            return []
    else:
        logger.info(f"{error = }".encode("UTF-8"))
    logger.info(f"{search_results = }".encode("UTF-8"))
    return search_results
