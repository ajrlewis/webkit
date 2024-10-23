import random
import re
from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype
import httpx
from loguru import logger

import urllib.parse

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
    headers = random.choice(list_of_headers)
    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"{e = }")
    else:
        return response


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
    return visible_text


def text_from_url(url: str) -> dict:
    logger.debug(f"{url = }")
    sanitized_url = sanitize_url(url)
    logger.debug(f"{sanitized_url = }")
    response = get_response(sanitized_url)
    logger.debug(f"{response = }")
    text = ""
    if response:
        redirected_url = response.url
        logger.debug(f"{redirected_url = }")
        body = response.text
        text = text_from_html(body)
        logger.debug(f"{text = }")
        return {
            "sanitized_url": sanitized_url,
            "redirected_url": f"{redirected_url}",
            "text": text,
        }
    return {
        "sanitized_url": sanitized_url,
        "redirected_url": f"{redirected_url}",
        "text": text,
    }
