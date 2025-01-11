from loguru import logger

from . import scrape
from . import search


def google(query: str, max_results: int = 10) -> list[dict]:
    results = search.google(query=query, max_results=max_results)
    logger.debug(f"{results = }".encode("UTF-8"))
    deep_results = []
    for result in results.get("results", []):
        if href := result.get("href"):
            logger.debug(f"{href = }")
            data = scrape.data_from_url(url=href)
            logger.debug(f"{data = }".encode("UTF-8"))
            if body := data.get("text"):
                deep_result = result | {"body": body}
                deep_results.append(deep_result)
    return deep_results
