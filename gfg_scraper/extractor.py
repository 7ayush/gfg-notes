"""Content extraction module for isolating article body from GfG pages."""

import logging
import re

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Tags to strip from extracted article content
_UNWANTED_TAGS = {"nav", "aside", "footer", "header"}

# Regex pattern matching ad-related CSS class names
_AD_CLASS_PATTERN = re.compile(r"ad|advertisement|sidebar", re.IGNORECASE)

# Fallback selectors for main content div (class or id patterns)
_CONTENT_CLASS_PATTERN = re.compile(r"article|content|entry", re.IGNORECASE)
_CONTENT_ID_CANDIDATES = {"main-content"}


def _strip_unwanted_elements(content: Tag) -> None:
    """Remove nav, aside, footer, header tags and ad-class elements in place."""
    # Remove unwanted tags
    for tag_name in _UNWANTED_TAGS:
        for element in content.find_all(tag_name):
            element.decompose()

    # Remove elements with ad-related classes
    for element in content.find_all(class_=_AD_CLASS_PATTERN):
        element.decompose()


def _find_main_content_div(soup: BeautifulSoup) -> Tag | None:
    """Find a main content div by class pattern or id.

    Uses a priority-ordered search:
    1. GfG-specific selectors (most precise)
    2. Generic class/id patterns (fallback)
    """
    # --- GfG-specific selectors (highest priority) ---
    # The actual article text lives in div.content inside the article--viewer
    match = soup.find("div", class_="content")
    if match:
        return match

    # article--viewer wraps the article header + content
    match = soup.find(
        "div",
        class_=lambda c: c and "article--viewer" in (
            " ".join(c) if isinstance(c, list) else c
        ),
    )
    if match:
        return match

    # --- Generic fallback selectors ---
    # Use a stricter pattern that requires the class to be exactly "content",
    # "article-body", "entry-content", etc. — not a substring of a layout class
    for cls in ("article-body", "entry-content", "post-content"):
        match = soup.find("div", class_=cls)
        if match:
            return match

    # Try matching by id
    for candidate_id in _CONTENT_ID_CANDIDATES:
        match = soup.find("div", id=candidate_id)
        if match:
            return match

    return None


def _convert_gfg_custom_elements(content: Tag) -> None:
    """Convert GfG custom elements to standard HTML in place.

    GfG uses ``<gfg-carousel-content>`` instead of ``<img>`` for images.
    Convert them to standard ``<img>`` tags so markdownify can handle them.
    """
    # Use a temporary soup to create new tags reliably
    tag_factory = BeautifulSoup("", "html.parser")

    for carousel_content in content.find_all("gfg-carousel-content"):
        src = carousel_content.get("src", "")
        alt = carousel_content.get("alt", "")
        if src:
            img_tag = tag_factory.new_tag("img", src=src, alt=alt)
            carousel_content.replace_with(img_tag)

    # Remove the carousel wrapper, keeping its children
    for carousel in content.find_all("gfg-carousel"):
        carousel.unwrap()


def _extract_from_next_data(soup: BeautifulSoup) -> Tag | None:
    """Try to extract article content from __NEXT_DATA__ JSON.

    GfG renders article content client-side from JSON embedded in a script tag.
    This contains the full article HTML including custom image elements that
    aren't present in the server-rendered div.content.
    """
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return None

    try:
        import json
        data = json.loads(script.string)
        post_content = (
            data.get("props", {})
            .get("pageProps", {})
            .get("postDataFromWriteApi", {})
            .get("post_content", "")
        )
        if not post_content:
            return None

        content_soup = BeautifulSoup(post_content, "html.parser")
        # Wrap in a div if it's just fragments
        wrapper = BeautifulSoup("<div></div>", "html.parser").div
        for child in list(content_soup.children):
            wrapper.append(child)
        return wrapper
    except Exception:
        return None


def extract_article_content(html: str, url: str) -> BeautifulSoup | None:
    """Parse HTML and return a BeautifulSoup tag containing only the article content.

    Looks for an ``<article>`` tag first, then falls back to a main content
    ``<div>`` identified by class or id patterns.  Strips navigation, sidebar,
    footer, header, and advertisement elements from the result.

    Returns ``None`` if no article structure is found (logs a warning).
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Try <article> tag first
    article = soup.find("article")

    # 2. Fallback to main content div
    if article is None:
        article = _find_main_content_div(soup)

    # 2b. If div.content was found but has no images, try __NEXT_DATA__
    #     which contains the full article HTML with custom image elements
    if article is not None and not article.find_all("img"):
        next_data_content = _extract_from_next_data(soup)
        if next_data_content and (
            next_data_content.find_all("gfg-carousel-content")
            or next_data_content.find_all("img")
        ):
            article = next_data_content

    # 3. Nothing found – log warning and return None
    if article is None:
        logger.warning("Article structure not found for URL: %s", url)
        return None

    # 4. Convert GfG custom elements (carousel images) to standard HTML
    _convert_gfg_custom_elements(article)

    # 5. Strip unwanted elements from the content
    _strip_unwanted_elements(article)

    # 5. Prepend the article title if it exists outside the content div
    #    GfG puts the <h1> in a separate ArticleHeader div, not inside div.content
    if article.find("h1") is None:
        title_h1 = soup.find("h1")
        if title_h1:
            article.insert(0, title_h1)

    return article
