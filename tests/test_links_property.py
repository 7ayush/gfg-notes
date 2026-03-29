"""Property-based tests for the links module.

Feature: gfg-web-scraper, Property 3: Link filtering only passes valid internal GfG links
Feature: gfg-web-scraper, Property 4: URL normalization is idempotent and strips query/fragment
"""

from urllib.parse import urlparse

from bs4 import BeautifulSoup
from hypothesis import given, settings
from hypothesis import strategies as st

from gfg_scraper.links import extract_internal_links, normalize_url


# ---------------------------------------------------------------------------
# Strategies for Property 3 – link filtering
# ---------------------------------------------------------------------------

_filter_schemes = st.sampled_from(["http", "https", "ftp", "mailto", "javascript", "data"])
_filter_domains = st.sampled_from([
    "geeksforgeeks.org",
    "www.geeksforgeeks.org",
    "practice.geeksforgeeks.org",
    "example.com",
    "google.com",
    "stackoverflow.com",
])
_filter_paths = st.from_regex(r"/[a-z0-9\-/]{0,40}", fullmatch=True)
_filter_fragments = st.one_of(
    st.just(""),
    st.from_regex(r"[a-z0-9]{1,10}", fullmatch=True),
)
_filter_queries = st.one_of(
    st.just(""),
    st.from_regex(r"[a-z]{1,6}=[a-z0-9]{1,6}", fullmatch=True),
)


@st.composite
def random_href(draw):
    """Generate a random href value for an <a> tag."""
    choice = draw(st.sampled_from(["full_url", "anchor_only"]))
    if choice == "anchor_only":
        frag = draw(st.from_regex(r"[a-z]{1,10}", fullmatch=True))
        return f"#{frag}"

    scheme = draw(_filter_schemes)
    domain = draw(_filter_domains)
    path = draw(_filter_paths)
    query = draw(_filter_queries)
    fragment = draw(_filter_fragments)

    url = f"{scheme}://{domain}{path}"
    if query:
        url += f"?{query}"
    if fragment:
        url += f"#{fragment}"
    return url


@st.composite
def html_with_random_links(draw):
    """Generate an HTML snippet with 1-10 <a> tags containing random hrefs."""
    num_links = draw(st.integers(min_value=1, max_value=10))
    hrefs = [draw(random_href()) for _ in range(num_links)]
    anchors = "".join(f'<a href="{h}">link</a>' for h in hrefs)
    return f"<div>{anchors}</div>"


@given(html=html_with_random_links())
@settings(max_examples=100)
def test_link_filtering_only_passes_valid_internal_gfg_links(html):
    """Property 3: Link filtering only passes valid internal GfG links.

    Validates: Requirements 3.2, 3.3

    For any set of URLs embedded in article HTML, extract_internal_links
    should return only those with HTTP(S) scheme and geeksforgeeks.org domain.
    Returned URLs must also be normalized (no query params or fragments).
    """
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://www.geeksforgeeks.org/"
    result = extract_internal_links(soup, base_url)

    for url in result:
        parsed = urlparse(url)
        # Only http or https scheme
        assert parsed.scheme in ("http", "https"), f"Bad scheme: {url}"
        # Domain must be geeksforgeeks.org
        assert parsed.hostname is not None and parsed.hostname.endswith(
            "geeksforgeeks.org"
        ), f"Bad domain: {url}"
        # Normalization applied – no query params or fragments
        assert "?" not in url, f"Query param found: {url}"
        assert "#" not in url, f"Fragment found: {url}"


# Strategy: generate URLs with random query params and fragments
_schemes = st.sampled_from(["http", "https"])
_domains = st.sampled_from([
    "geeksforgeeks.org",
    "www.geeksforgeeks.org",
    "example.com",
])
_paths = st.from_regex(r"/[a-z0-9\-/]{0,60}", fullmatch=True)
_query_params = st.one_of(
    st.just(""),
    st.from_regex(r"[a-z]{1,8}=[a-z0-9]{1,8}(&[a-z]{1,8}=[a-z0-9]{1,8}){0,3}", fullmatch=True),
)
_fragments = st.one_of(
    st.just(""),
    st.from_regex(r"[a-z0-9\-]{1,20}", fullmatch=True),
)


@st.composite
def urls_with_query_and_fragment(draw):
    """Generate URLs that may include query parameters and/or fragments."""
    scheme = draw(_schemes)
    domain = draw(_domains)
    path = draw(_paths)
    query = draw(_query_params)
    fragment = draw(_fragments)

    url = f"{scheme}://{domain}{path}"
    if query:
        url += f"?{query}"
    if fragment:
        url += f"#{fragment}"
    return url


@given(url=urls_with_query_and_fragment())
@settings(max_examples=100)
def test_url_normalization_idempotent_and_strips_query_fragment(url):
    """Property 4: URL normalization is idempotent and strips query/fragment.

    Validates: Requirements 3.4

    For any URL, normalizing it should:
    1. Remove all query parameters and fragment identifiers
    2. Be idempotent: normalize(normalize(url)) == normalize(url)
    """
    normalized = normalize_url(url)

    # Idempotence: applying normalize twice yields the same result
    assert normalize_url(normalized) == normalized

    # No query parameters or fragments remain
    assert "?" not in normalized
    assert "#" not in normalized
