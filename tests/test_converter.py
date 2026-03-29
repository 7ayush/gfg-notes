"""Unit tests for gfg_scraper.converter module.

Tests cover:
- Conversion of headings (h1-h6)
- Conversion of code blocks
- Conversion of unordered and ordered lists
- Conversion of tables
- Conversion of bold/italic text
- Conversion of images
- Handling of empty content

Requirements: 2.1, 2.3
"""

from bs4 import BeautifulSoup

from gfg_scraper.converter import convert_to_markdown


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Headings (Requirement 2.3 – preserve semantic structure)
# ---------------------------------------------------------------------------


class TestHeadings:
    """Headings h1-h6 should produce ATX-style Markdown markers."""

    def test_h1(self):
        md = convert_to_markdown(_soup("<h1>Title</h1>"))
        assert md.startswith("# ")
        assert "Title" in md

    def test_h2(self):
        md = convert_to_markdown(_soup("<h2>Section</h2>"))
        assert "## " in md
        assert "Section" in md

    def test_h3(self):
        md = convert_to_markdown(_soup("<h3>Subsection</h3>"))
        assert "### " in md

    def test_h6(self):
        md = convert_to_markdown(_soup("<h6>Deep</h6>"))
        assert "###### " in md


# ---------------------------------------------------------------------------
# Code blocks (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestCodeBlocks:
    """<pre><code> blocks should produce fenced or indented code."""

    def test_code_block(self):
        md = convert_to_markdown(_soup("<pre><code>print('hi')</code></pre>"))
        assert "```" in md or "    print" in md
        assert "print" in md

    def test_inline_code(self):
        md = convert_to_markdown(_soup("<p>Use <code>len()</code> here</p>"))
        assert "`len()`" in md


# ---------------------------------------------------------------------------
# Lists (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestLists:
    """Unordered and ordered lists should produce correct markers."""

    def test_unordered_list(self):
        html = "<ul><li>Apple</li><li>Banana</li></ul>"
        md = convert_to_markdown(_soup(html))
        lines = [l.strip() for l in md.splitlines() if l.strip()]
        assert any(l.startswith("*") or l.startswith("-") for l in lines)
        assert "Apple" in md
        assert "Banana" in md

    def test_ordered_list(self):
        html = "<ol><li>First</li><li>Second</li></ol>"
        md = convert_to_markdown(_soup(html))
        assert "1." in md
        assert "First" in md
        assert "Second" in md


# ---------------------------------------------------------------------------
# Tables (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestTables:
    """HTML tables should produce pipe-delimited Markdown tables."""

    def test_simple_table(self):
        html = (
            "<table>"
            "<thead><tr><th>Name</th><th>Age</th></tr></thead>"
            "<tbody><tr><td>Alice</td><td>30</td></tr></tbody>"
            "</table>"
        )
        md = convert_to_markdown(_soup(html))
        assert "|" in md
        assert "Name" in md
        assert "Alice" in md


# ---------------------------------------------------------------------------
# Bold / Italic (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestBoldItalic:
    """Bold and italic text should produce ** and * markers."""

    def test_strong_tag(self):
        md = convert_to_markdown(_soup("<p><strong>bold</strong></p>"))
        assert "**bold**" in md

    def test_b_tag(self):
        md = convert_to_markdown(_soup("<p><b>bold</b></p>"))
        assert "**bold**" in md

    def test_em_tag(self):
        md = convert_to_markdown(_soup("<p><em>italic</em></p>"))
        assert "*italic*" in md

    def test_i_tag(self):
        md = convert_to_markdown(_soup("<p><i>italic</i></p>"))
        assert "*italic*" in md


# ---------------------------------------------------------------------------
# Images (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestImages:
    """Images should produce ![alt](src) Markdown syntax."""

    def test_image_with_alt(self):
        html = '<img src="https://example.com/pic.png" alt="diagram" />'
        md = convert_to_markdown(_soup(html))
        assert "![diagram]" in md
        assert "https://example.com/pic.png" in md

    def test_image_without_alt(self):
        html = '<img src="https://example.com/pic.png" />'
        md = convert_to_markdown(_soup(html))
        assert "![" in md
        assert "https://example.com/pic.png" in md


# ---------------------------------------------------------------------------
# Empty content (Requirement 2.1)
# ---------------------------------------------------------------------------


class TestEmptyContent:
    """Empty or whitespace-only HTML should return an empty string."""

    def test_empty_div(self):
        md = convert_to_markdown(_soup("<div></div>"))
        assert md == ""

    def test_whitespace_only(self):
        md = convert_to_markdown(_soup("<div>   \n  </div>"))
        assert md == ""
