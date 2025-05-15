import datetime
import random
import re
from typing import Optional
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, Tag
import fake_useragent
import httpx
from loguru import logger


def sanitize_url(url: str) -> str:
    logger.debug(f"{url = }")
    if not urllib.parse.urlparse(url).scheme:
        if "http" in url:
            url = url.replace("http", "")
        else:
            url = "http://" + url
    return url


def _is_element_visible(element: Doctype) -> bool:
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


def get_response(
    url: str, params: Optional[dict] = None, headers: dict = {}, timeout: int = 20
) -> tuple[Optional[httpx.Response], Optional[str]]:
    logger.debug(f"{url = }")
    ua = fake_useragent.UserAgent()
    headers = headers | {"User-Agent": ua.random}
    cookies = {"session_id": "1234567890"}
    timeout = httpx.Timeout(timeout)
    logger.debug(f"{headers = } {cookies = } {timeout = }")
    response = None
    error = None
    try:
        response = httpx.get(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=True,
        )
        logger.debug(f"{response = }")
        logger.debug(f"{response.text = }")
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


def _text_from_soup(soup: BeautifulSoup, max_words: int = 1000) -> str:
    # Get all text
    texts = soup.findAll(string=True)
    # Only get visible text
    visible_texts = filter(_is_element_visible, texts)
    visible_text = " ".join(visible_text.strip() for visible_text in visible_texts)
    # Remove excessive white space.
    visible_text = visible_text.strip()
    visible_text = re.sub(" +", " ", visible_text)
    # Crop to maximum words
    visible_words = visible_text.split(" ")
    visible_words = visible_words[:max_words]
    visible_text = " ".join(visible_words)
    # Encode text
    visible_text = visible_text.encode("utf-8")
    return visible_text


def _images_from_soup(soup: BeautifulSoup, root_url: str = "") -> list[dict]:
    tags = soup.find_all("img")
    images = []
    for tags in tags:
        attrs = tags.attrs
        if alt := attrs.get("alt"):
            if src := attrs.get("src"):
                if src.startswith("/") and root_url:
                    src = f"{root_url}{src}"
                images.append({"alt": alt, "src": src})
    return images


def _anchors_from_soup(soup: BeautifulSoup, root_url: str = "") -> list[dict]:
    tags = soup.find_all("a", href=True)
    hrefs = []
    for tag in tags:
        if href := tag.get("href"):
            if href.startswith("#") or len(href) <= 1:
                continue
            if href.endswith("/"):
                href = href[:-1]
            if href.startswith("/") and root_url:
                href = f"{root_url}{href}"
            hrefs.append(href)
    hrefs = sorted(list(set(hrefs)))
    anchors = [{"href": href} for href in hrefs]
    return anchors


def _soup_from_markup(markup: str, features: str = "html.parser") -> BeautifulSoup:
    soup = BeautifulSoup(markup=markup, features=features)
    return soup


def data_from_url(url: str) -> dict:
    logger.debug(f"{url = }")
    sanitized_url = sanitize_url(url)
    logger.debug(f"{sanitized_url = }")
    data = {
        "url": url,
        "sanitized_url": sanitized_url,
        "redirected_url": None,
        "text": None,
        "image_tags": None,
        "anchor_tags": None,
        "error": None,
        "is_reachable": True,
        "scraped_on": datetime.datetime.utcnow(),
    }
    response, error = get_response(sanitized_url)
    content_type = response.headers.get("Content-Type")
    if "text/html" not in content_type:
        logger.error(f"{content_type = }")
        error = 'Content type is not "text/html"'
    logger.debug(f"{response = } {content_type = }")
    if error:
        data["error"] = error
        data["is_reachable"] = False
    else:
        redirected_url = response.url
        logger.debug(f"{redirected_url = }")
        body = response.text
        soup = _soup_from_markup(markup=body, features="html.parser")
        text = _text_from_soup(soup)
        images = _images_from_soup(soup, root_url=redirected_url)
        anchors = _anchors_from_soup(soup, root_url=redirected_url)
        data["text"] = text
        data["image_tags"] = images
        data["anchor_tags"] = anchors
        data["redirected_url"] = f"{redirected_url}"
    return data


def data_from_search_result(search_result: dict) -> Optional[dict]:
    if href := search_result.get("href"):
        logger.debug(f"{href = }".encode("UTF-8"))
        data = scrape.data_from_url(url=href)
        return data
