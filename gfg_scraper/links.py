# Link discovery and normalization module

from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    """Remove query parameters and fragments from a URL."""
    parsed = urlparse(url)
    cleaned = parsed._replace(query="", fragment="")
    return urlunparse(cleaned)


def extract_internal_links(article_soup: BeautifulSoup, base_url: str) -> list[str]:
    """
    Extract all internal GfG links from article content.
    Normalizes URLs (removes query params, fragments).
    Filters out external, anchor-only, and non-HTTP(S) links.
    Returns deduplicated list preserving discovery order.
    """
    seen: set[str] = set()
    result: list[str] = []

    for anchor in article_soup.find_all("a", href=True):
        href = anchor["href"].strip()

        # Reject anchor-only links
        if not href or href.startswith("#"):
            continue

        # Reject mailto: and javascript: schemes
        if href.lower().startswith(("mailto:", "javascript:")):
            continue

        # Resolve relative URLs against the base URL
        absolute = urljoin(base_url, href)

        parsed = urlparse(absolute)

        # Accept only http/https schemes
        if parsed.scheme not in ("http", "https"):
            continue

        # Accept only geeksforgeeks.org domain
        if not parsed.hostname or not parsed.hostname.endswith("geeksforgeeks.org"):
            continue

        normalized = normalize_url(absolute)

        # Deduplicate while preserving discovery order
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result
