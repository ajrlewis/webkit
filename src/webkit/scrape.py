import datetime
import random
import re
from typing import Optional
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype
import fake_useragent
import httpx
from loguru import logger


def sanitize_url(url: str) -> str:
    if not urllib.parse.urlparse(url).scheme:
        if "http" in url:
            url = url.replace("http", "")
        else:
            url = "http://" + url
    return url


def get_response(url: str) -> tuple[Optional[httpx.Response], Optional[str]]:
    logger.debug(f"{url = }")
    ua = fake_useragent.UserAgent()
    headers = {"User-Agent": ua.random}
    logger.debug(f"{headers = }")
    cookies = {"session_id": "1234567890"}
    logger.debug(f"{cookies = }")
    response = None
    error = None
    try:
        response = httpx.get(
            url, headers=headers, cookies=cookies, follow_redirects=True
        )
        logger.debug(f"{response = }")
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        error = f"Error making request to {url}: {e}"
        logger.error(error)
    except httpx.TimeoutException as e:
        error = f"Timeout error making request to {url}: {e}"
        logger.error(error)
    except httpx.ConnectError as e:
        error = f"Connection error making request to {url}: {e}"
        logger.error(error)
    except Exception as e:
        error = f"Unknown error making request to {url}: {e}"
        logger.error(error)
    return response, error


def tag_visible(element: Doctype) -> bool:
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(markup: str, features: str = "html.parser") -> str:
    soup = BeautifulSoup(markup=markup, features=features)
    texts = soup.findAll(string=True)
    visible_texts = filter(tag_visible, texts)
    visible_text = " ".join(visible_text.strip() for visible_text in visible_texts)
    visible_text = visible_text.strip()
    visible_text = re.sub(" +", " ", visible_text)
    return visible_text


def text_from_url(url: str) -> dict:
    logger.debug(f"{url = }")
    sanitized_url = sanitize_url(url)
    logger.debug(f"{sanitized_url = }")
    data = {
        "url": url,
        "sanitized_url": sanitized_url,
        "redirected_url": None,
        "text": None,
        "error": None,
        "is_reachable": True,
        "scraped_on": f"{datetime.datetime.now(datetime.UTC)}",
    }
    logger.debug(f"{data = }")
    response, error = get_response(sanitized_url)
    logger.debug(f"{response = }")
    if error:
        data["error"] = error
        data["is_reachable"] = False
    else:
        redirected_url = response.url
        logger.debug(f"{redirected_url = }")
        body = response.text
        text = text_from_html(body)
        logger.debug(f"{text = }")
        data["redirected_url"] = f"{redirected_url}"
        data["text"] = text
    return data
