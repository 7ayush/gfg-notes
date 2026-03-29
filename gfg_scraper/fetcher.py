"""HTTP fetcher module with polite request behavior."""

import logging
import time

import requests

from gfg_scraper.config import ScraperConfig

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def fetch_page(url: str, config: ScraperConfig) -> str | None:
    """
    Fetch a URL and return the HTML content as a string.
    Returns None on error (logs the error).
    Applies polite delay before each request.
    """
    time.sleep(config.polite_delay)

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=config.request_timeout)
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching %s", url)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error fetching %s", url)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("Request error fetching %s: %s", url, exc)
        return None

    if not response.ok:
        logger.error("Non-2xx status %d for %s", response.status_code, url)
        return None

    return response.text
