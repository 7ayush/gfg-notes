"""Unit tests for gfg_scraper.links module.

Tests cover:
- URL normalization (query params, fragments, both, neither)
- Link filtering (external domains, anchor-only, mailto, javascript)
- Deduplication and discovery order preservation

Requirements: 3.1, 3.2, 3.3, 3.4
"""

from bs4 import BeautifulSoup

from gfg_scraper.links import extract_internal_links, normalize_url


# ---------------------------------------------------------------------------
# normalize_url tests
# ---------------------------------------------------------------------------


class TestNormalizeUrl:
    def test_strips_query_params(self):
        url = "https://www.geeksforgeeks.org/arrays/?ref=lbp"
        assert normalize_url(url) == "https://www.geeksforgeeks.org/arrays/"

    def test_strips_fragment(self):
        url = "https://www.geeksforgeeks.org/arrays/#section-2"
        assert normalize_url(url) == "https://www.geeksforgeeks.org/arrays/"

    def test_strips_both_query_and_fragment(self):
        url = "https://www.geeksforgeeks.org/arrays/?ref=lbp#top"
        assert normalize_url(url) == "https://www.geeksforgeeks.org/arrays/"

    def test_no_query_or_fragment_unchanged(self):
        url = "https://www.geeksforgeeks.org/arrays/"
        assert normalize_url(url) == url

    def test_preserves_scheme_and_domain(self):
        url = "http://practice.geeksforgeeks.org/path?q=1#frag"
        assert normalize_url(url) == "http://practice.geeksforgeeks.org/path"

    def test_multiple_query_params(self):
        url = "https://www.geeksforgeeks.org/page/?a=1&b=2&c=3"
        assert normalize_url(url) == "https://www.geeksforgeeks.org/page/"


# ---------------------------------------------------------------------------
# extract_internal_links – filtering tests
# ---------------------------------------------------------------------------


def _make_soup(hrefs: list[str]) -> BeautifulSoup:
    """Helper to build a BeautifulSoup from a list of href values."""
    anchors = "".join(f'<a href="{h}">link</a>' for h in hrefs)
    return BeautifulSoup(f"<div>{anchors}</div>", "html.parser")


BASE_URL = "https://www.geeksforgeeks.org/data-structures/"


class TestExtractInternalLinksFiltering:
    """Requirement 3.2, 3.3: only internal GfG HTTP(S) links pass."""

    def test_accepts_internal_gfg_link(self):
        soup = _make_soup(["https://www.geeksforgeeks.org/arrays/"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://www.geeksforgeeks.org/arrays/"]

    def test_accepts_subdomain_gfg_link(self):
        soup = _make_soup(["https://practice.geeksforgeeks.org/problems/"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://practice.geeksforgeeks.org/problems/"]

    def test_rejects_external_domain(self):
        soup = _make_soup(["https://stackoverflow.com/questions/"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == []

    def test_rejects_anchor_only_link(self):
        soup = _make_soup(["#section-1"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == []

    def test_rejects_mailto_link(self):
        soup = _make_soup(["mailto:user@example.com"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == []

    def test_rejects_javascript_link(self):
        soup = _make_soup(["javascript:void(0)"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == []

    def test_rejects_ftp_scheme(self):
        soup = _make_soup(["ftp://geeksforgeeks.org/file"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == []

    def test_resolves_relative_internal_link(self):
        soup = _make_soup(["/linked-list/"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://www.geeksforgeeks.org/linked-list/"]

    def test_normalizes_query_and_fragment_on_internal_link(self):
        soup = _make_soup(["https://www.geeksforgeeks.org/trees/?ref=lbp#intro"])
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://www.geeksforgeeks.org/trees/"]

    def test_mixed_links_filters_correctly(self):
        hrefs = [
            "https://www.geeksforgeeks.org/arrays/",
            "https://example.com/page",
            "#anchor",
            "mailto:a@b.com",
            "javascript:alert(1)",
            "https://practice.geeksforgeeks.org/problems/",
        ]
        soup = _make_soup(hrefs)
        result = extract_internal_links(soup, BASE_URL)
        assert result == [
            "https://www.geeksforgeeks.org/arrays/",
            "https://practice.geeksforgeeks.org/problems/",
        ]


# ---------------------------------------------------------------------------
# extract_internal_links – deduplication & order preservation
# ---------------------------------------------------------------------------


class TestExtractInternalLinksDedup:
    """Requirement 3.1, 3.4: deduplicated, discovery-order preserved."""

    def test_deduplicates_identical_urls(self):
        hrefs = [
            "https://www.geeksforgeeks.org/arrays/",
            "https://www.geeksforgeeks.org/arrays/",
        ]
        soup = _make_soup(hrefs)
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://www.geeksforgeeks.org/arrays/"]

    def test_deduplicates_after_normalization(self):
        hrefs = [
            "https://www.geeksforgeeks.org/arrays/?ref=lbp",
            "https://www.geeksforgeeks.org/arrays/#section",
            "https://www.geeksforgeeks.org/arrays/",
        ]
        soup = _make_soup(hrefs)
        result = extract_internal_links(soup, BASE_URL)
        assert result == ["https://www.geeksforgeeks.org/arrays/"]

    def test_preserves_discovery_order(self):
        hrefs = [
            "https://www.geeksforgeeks.org/trees/",
            "https://www.geeksforgeeks.org/arrays/",
            "https://www.geeksforgeeks.org/graphs/",
        ]
        soup = _make_soup(hrefs)
        result = extract_internal_links(soup, BASE_URL)
        assert result == [
            "https://www.geeksforgeeks.org/trees/",
            "https://www.geeksforgeeks.org/arrays/",
            "https://www.geeksforgeeks.org/graphs/",
        ]

    def test_empty_article_returns_empty_list(self):
        soup = BeautifulSoup("<div>No links here</div>", "html.parser")
        result = extract_internal_links(soup, BASE_URL)
        assert result == []
