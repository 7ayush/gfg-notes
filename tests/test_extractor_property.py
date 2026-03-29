"""Property-based tests for the extractor module.

Feature: gfg-web-scraper, Property 1: Article content extraction isolates the article body
"""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from gfg_scraper.extractor import extract_article_content


# ---------------------------------------------------------------------------
# Strategies for Property 1 – article content extraction
# ---------------------------------------------------------------------------

# Random text content for the article body
_article_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
    min_size=1,
    max_size=80,
)

# Unwanted tag names that should be stripped
_UNWANTED_TAGS = ["nav", "aside", "footer", "header"]

# Ad-related class names that should be stripped
_AD_CLASSES = ["ad", "advertisement", "sidebar"]


@st.composite
def unwanted_element(draw):
    """Generate a single unwanted HTML element (tag or ad-class div)."""
    choice = draw(st.sampled_from(["tag", "ad_class"]))
    inner_text = draw(_article_text)

    if choice == "tag":
        tag = draw(st.sampled_from(_UNWANTED_TAGS))
        return f"<{tag}><p>{inner_text}</p></{tag}>"
    else:
        cls = draw(st.sampled_from(_AD_CLASSES))
        return f'<div class="{cls}"><p>{inner_text}</p></div>'


@st.composite
def html_with_article_and_unwanted(draw):
    """Generate an HTML document with an <article> containing random content
    plus random unwanted elements injected inside it."""
    # Core article paragraph content
    num_paragraphs = draw(st.integers(min_value=1, max_value=5))
    paragraphs = "".join(
        f"<p>{draw(_article_text)}</p>" for _ in range(num_paragraphs)
    )

    # Random unwanted elements injected inside the article
    num_unwanted = draw(st.integers(min_value=1, max_value=6))
    unwanted_parts = "".join(
        draw(unwanted_element()) for _ in range(num_unwanted)
    )

    article_body = paragraphs + unwanted_parts
    return f"<html><body><article>{article_body}</article></body></html>"


# Regex to detect ad-related class values in the output
_AD_CLASS_PATTERN = re.compile(r'class="[^"]*\b(ad|advertisement|sidebar)\b[^"]*"', re.IGNORECASE)


@given(html=html_with_article_and_unwanted())
@settings(max_examples=100)
def test_article_content_extraction_isolates_article_body(html):
    """Property 1: Article content extraction isolates the article body.

    **Validates: Requirements 1.1, 1.2**

    For any HTML document containing an <article> tag with random content
    and injected unwanted elements (nav, aside, footer, header, ad divs),
    the extractor should return content with no unwanted tags or ad-class
    elements.
    """
    result = extract_article_content(html, "https://www.geeksforgeeks.org/test")

    assert result is not None, "Extractor should find the <article> tag"

    result_html = str(result)

    # Assert no unwanted tags remain
    for tag in _UNWANTED_TAGS:
        assert result.find(tag) is None, (
            f"Unwanted <{tag}> tag found in extracted content"
        )

    # Assert no ad-related class elements remain
    assert not _AD_CLASS_PATTERN.search(result_html), (
        f"Ad-related class found in extracted content: {result_html}"
    )
