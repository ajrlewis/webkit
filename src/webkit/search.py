from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import (
    DuckDuckGoSearchException,
    RatelimitException,
    TimeoutException,
)
from loguru import logger


def duckduckgo_search(keywords: str, max_results: int = 10) -> list[dict]:
    logger.debug(f"{keywords = } {max_results = }")
    try:
        results = DDGS().text(keywords, safesearch="off", max_results=max_results)
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
