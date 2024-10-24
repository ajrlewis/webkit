import datetime
import random
import re
from typing import Optional
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype
import httpx
from loguru import logger


list_of_headers = [
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    },
    {
        "User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3"
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.97 Safari/537.3"
    },
]


def sanitize_url(url: str) -> str:
    if not urllib.parse.urlparse(url).scheme:
        if "http" in url:
            url = url.replace("http", "")
        else:
            url = "http://" + url
    return url


def get_response(url: str) -> Optional[httpx.Response]:
    logger.debug(f"{url = }")
    headers = random.choice(list_of_headers)
    logger.debug(f"{headers = }")
    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"{e = }")
    else:
        return response


# Return error as well
# def get_response(url: str) -> Optional[httpx.Response], str:
#     headers = random.choice(list_of_headers)
#     try:
#         response = httpx.get(url, headers=headers, follow_redirects=True)
#         response.raise_for_status()
#         return response
#     except httpx.HTTPStatusError as e:
#         logger.error(f"Error making request to {url}: {e}")
#     except httpx.TimeoutException:
#         logger.error(f"Timeout error making request to {url}")
#     except httpx.ConnectionError:
#         logger.error(f"Connection error making request to {url}")
#     except Exception as e:
#         logger.error(f"Unknown error making request to {url}: {e}")


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
        "redirected_url": "",
        "text": "",
        "error": "",
        "scraped_on": f"{datetime.datetime.now(datetime.UTC)}",
    }
    logger.debug(f"{data = }")
    response = get_response(sanitized_url)
    logger.debug(f"{response = }")
    if response:
        redirected_url = response.url
        logger.debug(f"{redirected_url = }")
        body = response.text
        text = text_from_html(body)
        logger.debug(f"{text = }")
        data["text"] = text
        data["redirected_url"] = f"{redirected_url}"
    return data


x = text_from_url("ajrlewis.com")
logger.info(x)
