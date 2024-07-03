import datetime
import os
import random
import sys

from loguru import logger
from urllib.parse import urlparse
import urllib3
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers_list = [
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


def get_random_headers() -> dict:
    return random.choice(headers_list)


def sanitize_url(url: str) -> str:
    logger.debug(f"Sanitizing {url = }")
    url = url.strip()
    parsed_url = urlparse(url)

    # scheme
    scheme = parsed_url.scheme
    if not scheme:
        logger.debug(f"No scheme supplied, using https://")
        scheme = "https"
    logger.debug(f"{scheme = }")

    # get the network location
    network_location = parsed_url.netloc

    logger.debug(f"{network_location = }")
    logger.debug(f"{network_location = }")
    # if network_location[0] == "/":
    #     network_location = network_location[1:]
    logger.debug(f"{network_location = }")

    # get the resource path
    path = parsed_url.path
    path = path.replace("www.", "")
    logger.debug(f"{path = }")

    # generate the sanitized url
    sanitized_url = f"{scheme}://{network_location}/{path}"
    logger.debug(f"{sanitized_url = }")

    # get the query parameters
    query = parsed_url.query
    if query:
        sanitized_url = f"{sanitized_url}?{query}"

    #
    logger.debug(sanitized_url[-1])
    if sanitized_url[-1] == "/":
        sanitized_url = sanitized_url[:-1]

    # TODO (ajrl) This shouldn't happen
    sanitized_url = sanitized_url.replace("///", "//")

    logger.debug(f"{sanitized_url = }")

    return sanitized_url


def get_response(url: str) -> requests.models.Response:
    headers = get_random_headers()
    logger.debug(f"{headers = }")
    response = requests.get(
        url, headers=headers, verify=True, allow_redirects=True, timeout=20
    )
    logger.debug(f"{response = }")
    response.raise_for_status()
    return response


def check_website_exists(url: str) -> bool:
    try:
        _ = get_response(url)
        return True
    except requests.exceptions.RequestException:
        return False


def scrape_website_for_text(url: str) -> dict:
    logger.debug(f"Scraping website for text {url = }")

    data = {
        "url": "",
        "text": "",
        "content_type": "",
        "scraped_on": f"{datetime.datetime.utcnow()}",
        "is_reachable": False,
        "error": "",
    }

    # sanitize the  url
    try:
        url = sanitize_url(url)
    except:
        pass

    data["url"] = url

    # get the content type returned
    content_type = requests.head(url).headers["Content-Type"]
    data["content_type"] = content_type

    # get the website response
    try:
        response = get_response(url)
    except requests.exceptions.RequestException as e:
        logger.debug(f"Failed to get response {e = }")
        text, error = scrape_dynamic_website_for_text(url)
        data["text"] = text
        data["error"] = error
        is_reachable = len(text) > 0 and len(error) == 0
        data["is_reachable"] = is_reachable
        return data

    # get the content type returned
    content_type = response.headers.get("content-type", "")
    logger.debug(f"{content_type = }")
    data["content_type"] = content_type
    response_is_xml = "xml" in content_type
    if response_is_xml:
        parser = "lxml-xml"
        markup = response.content
    else:
        parser = "html.parser"
        markup = response.text

    # try to extract the text
    text = ""
    error = ""
    try:
        soup = BeautifulSoup(markup, parser)
        if response_is_xml:
            texts = []
            items = soup.find_all("item")
            for item in items:
                title = item.find("title").text.strip()
                description = item.find("description").text.strip()
                texts.append(f"{title}: {description}")
            text = "\n".join(texts)
        else:
            text = soup.body.get_text(" ", strip=True)
    except Exception as e:
        data["error"] = f"BeautifulSoup unable to extract body from response text {e}."
        return data

    # remove excessive white space
    text = " ".join([t for t in text.split(" ") if t])

    # Check if the website is reachable
    is_reachable = len(text) > 0 and len(error) == 0

    # check if the website is dynamic
    if not text:
        logger.debug(f"{text = }")
        text, error = scrape_dynamic_website_for_text(url)
        if text:
            data["text"] = text
            return data
        data["error"] = f"{error}"
        return data

    data["text"] = text

    return data


def scrape_dynamic_website_for_text(url: str) -> tuple[str]:
    logger.debug(f"Scraping dynamic website for text {url = }")

    firefox_service = Service()
    logger.debug(f"{firefox_service = }")

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-gpu")
    firefox_options.add_argument("--window-size=1280x1696")
    firefox_options.add_argument("--hide-scrollbars")
    firefox_options.add_argument("--enable-logging")
    firefox_options.add_argument("--log-level=0")
    firefox_options.add_argument("--v=99")
    firefox_options.add_argument("--single-process")
    firefox_options.add_argument("--ignore-certificate-errors")
    headers = get_random_headers()
    firefox_options.add_argument(f"user-agent={headers['User-Agent']}")

    logger.debug(f"{firefox_options = }")

    try:
        driver = webdriver.Firefox(
            service=firefox_service,
            options=firefox_options,
        )
    except Exception as e:
        logger.debug(f"Scraping failed {e = }")
        return "", f"{e}"

    driver.get(url)

    texts = []
    tag_names = ["h1", "h2", "h3", "h4", "p"]
    for tag_name in tag_names:
        elements = driver.find_elements(By.TAG_NAME, tag_name)
        for element in elements:
            text = element.text
            if text:
                texts.append(text)
    text = " ".join(texts)
    error = "" if text else "Failed to scrape dynamic website for text."
    return text, error


def main():
    logger.debug(f"{sys.argv = }")
    url = sys.argv[1]
    data = scrape_website_for_text(url)
    print(data)


if __name__ == "__main__":
    main()
