from duckduckgo_search import DDGS
from loguru import logger


def duckduckgo_search(keywords: str, max_results: int = 10) -> list[dict]:
    try:
        results = DDGS().text(keywords, safesearch="off", max_results=max_results)
    except Exception as e:
        # DuckDuckGoSearchException
        # RatelimitException
        # TimeoutException
        logger.error(f"{e = }")
        results = []
    return results
