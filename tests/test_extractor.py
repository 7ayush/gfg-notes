"""Unit tests for gfg_scraper.extractor module.

Tests cover:
- Extraction from HTML with <article> tag
- Fallback to main content <div> when no <article> tag
- None return and warning log when no article structure found
- Stripping of sidebar, nav, footer, header, ad elements

Requirements: 1.1, 1.2, 1.3
"""

import logging

from gfg_scraper.extractor import extract_article_content


URL = "https://www.geeksforgeeks.org/test-page/"


# ---------------------------------------------------------------------------
# Extraction via <article> tag (Requirement 1.1)
# ---------------------------------------------------------------------------


class TestArticleTagExtraction:
    """Requirement 1.1: identify Article_Content by targeting <article> tag."""

    def test_extracts_article_tag_content(self):
        html = "<html><body><article><p>Hello world</p></article></body></html>"
        result = extract_article_content(html, URL)
        assert result is not None
        assert result.name == "article"
        assert result.find("p").get_text() == "Hello world"

    def test_prefers_article_tag_over_content_div(self):
        html = (
            "<html><body>"
            '<div class="content"><p>Div content</p></div>'
            "<article><p>Article content</p></article>"
            "</body></html>"
        )
        result = extract_article_content(html, URL)
        assert result is not None
        assert result.name == "article"
        assert "Article content" in result.get_text()


# ---------------------------------------------------------------------------
# Fallback to main content <div> (Requirement 1.1)
# ---------------------------------------------------------------------------


class TestFallbackContentDiv:
    """Requirement 1.1: fall back to main content <div> when no <article>."""

    def test_fallback_to_div_with_content_class(self):
        html = '<html><body><div class="content"><p>Fallback</p></div></body></html>'
        result = extract_article_content(html, URL)
        assert result is not None
        assert result.name == "div"
        assert "Fallback" in result.get_text()

    def test_fallback_to_div_with_article_body_class(self):
        html = '<html><body><div class="article-body"><p>Body</p></div></body></html>'
        result = extract_article_content(html, URL)
        assert result is not None
        assert "Body" in result.get_text()

    def test_fallback_to_div_with_entry_content_class(self):
        html = '<html><body><div class="entry-content"><p>Entry</p></div></body></html>'
        result = extract_article_content(html, URL)
        assert result is not None
        assert "Entry" in result.get_text()

    def test_fallback_to_article_viewer_class(self):
        """GfG uses article--viewer class for the article wrapper."""
        html = (
            '<html><body>'
            '<div class="leftbar">Sidebar</div>'
            '<div class="some-class article--viewer">'
            '<p>Article content here</p>'
            '</div>'
            '</body></html>'
        )
        result = extract_article_content(html, URL)
        assert result is not None
        assert "Article content here" in result.get_text()

    def test_gfg_layout_extracts_content_div_not_outer_container(self):
        """GfG's outer container has 'Article' in class name — should NOT match.
        The inner div.content should be found instead."""
        html = (
            '<html><body>'
            '<div class="ArticlePagePostLayout_containerFluid__q38gg">'
            '<div class="LeftbarContainer">Sidebar links</div>'
            '<div class="article--viewer">'
            '<div class="content"><p>Real article</p></div>'
            '</div>'
            '<div class="RightBar">Ads</div>'
            '</div>'
            '</body></html>'
        )
        result = extract_article_content(html, URL)
        assert result is not None
        assert "Real article" in result.get_text()
        assert "Sidebar links" not in result.get_text()
        assert "Ads" not in result.get_text()

    def test_fallback_to_div_with_main_content_id(self):
        html = '<html><body><div id="main-content"><p>Main</p></div></body></html>'
        result = extract_article_content(html, URL)
        assert result is not None
        assert "Main" in result.get_text()


# ---------------------------------------------------------------------------
# None return and warning log (Requirement 1.3)
# ---------------------------------------------------------------------------


class TestNoArticleStructure:
    """Requirement 1.3: log warning and return None when structure not found."""

    def test_returns_none_when_no_article_structure(self):
        html = "<html><body><div><p>Random page</p></div></body></html>"
        result = extract_article_content(html, URL)
        assert result is None

    def test_logs_warning_when_no_article_structure(self, caplog):
        html = "<html><body><div><p>No article here</p></div></body></html>"
        with caplog.at_level(logging.WARNING):
            extract_article_content(html, URL)
        assert any("Article structure not found" in msg for msg in caplog.messages)
        assert any(URL in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# Stripping unwanted elements (Requirement 1.2)
# ---------------------------------------------------------------------------


class TestStrippingUnwantedElements:
    """Requirement 1.2: strip sidebars, nav, footer, header, ad elements."""

    def test_strips_nav_element(self):
        html = "<html><body><article><nav>Menu</nav><p>Content</p></article></body></html>"
        result = extract_article_content(html, URL)
        assert result is not None
        assert result.find("nav") is None
        assert "Content" in result.get_text()

    def test_strips_aside_element(self):
        html = "<html><body><article><aside>Sidebar</aside><p>Content</p></article></body></html>"
        result = extract_article_content(html, URL)
        assert result.find("aside") is None

    def test_strips_footer_element(self):
        html = "<html><body><article><footer>Footer</footer><p>Content</p></article></body></html>"
        result = extract_article_content(html, URL)
        assert result.find("footer") is None

    def test_strips_header_element(self):
        html = "<html><body><article><header>Header</header><p>Content</p></article></body></html>"
        result = extract_article_content(html, URL)
        assert result.find("header") is None

    def test_strips_ad_class_element(self):
        html = '<html><body><article><div class="ad">Ad</div><p>Content</p></article></body></html>'
        result = extract_article_content(html, URL)
        assert result.find("div", class_="ad") is None
        assert "Content" in result.get_text()

    def test_strips_advertisement_class_element(self):
        html = '<html><body><article><div class="advertisement">Ad</div><p>Content</p></article></body></html>'
        result = extract_article_content(html, URL)
        assert result.find("div", class_="advertisement") is None

    def test_strips_sidebar_class_element(self):
        html = '<html><body><article><div class="sidebar">Side</div><p>Content</p></article></body></html>'
        result = extract_article_content(html, URL)
        assert result.find("div", class_="sidebar") is None

    def test_strips_multiple_unwanted_elements(self):
        html = (
            "<html><body><article>"
            "<nav>Nav</nav>"
            "<header>Head</header>"
            '<div class="ad">Ad</div>'
            "<p>Real content</p>"
            "<footer>Foot</footer>"
            "</article></body></html>"
        )
        result = extract_article_content(html, URL)
        assert result is not None
        assert result.find("nav") is None
        assert result.find("header") is None
        assert result.find("footer") is None
        assert result.find("div", class_="ad") is None
        assert "Real content" in result.get_text()
