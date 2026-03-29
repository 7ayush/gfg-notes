"""Property-based tests for the converter module.

Feature: gfg-web-scraper, Property 2: Markdown conversion preserves semantic structure
"""

from bs4 import BeautifulSoup
from hypothesis import given, settings
from hypothesis import strategies as st

from gfg_scraper.converter import convert_to_markdown


# ---------------------------------------------------------------------------
# Strategies for Property 2 – Markdown conversion preserves semantic structure
# ---------------------------------------------------------------------------

_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=40,
)

_heading_levels = st.integers(min_value=1, max_value=6)

# Each element builder returns (html_snippet, element_type) so we can
# assert the right Markdown markers for whichever elements were included.


@st.composite
def heading_element(draw):
    """Generate a random heading (h1-h6)."""
    level = draw(_heading_levels)
    text = draw(_text)
    return f"<h{level}>{text}</h{level}>", "heading", level


@st.composite
def code_block_element(draw):
    """Generate a <pre><code> block."""
    code = draw(_text)
    return f"<pre><code>{code}</code></pre>", "code", None


@st.composite
def unordered_list_element(draw):
    """Generate an unordered list with 1-4 items."""
    n = draw(st.integers(min_value=1, max_value=4))
    items = "".join(f"<li>{draw(_text)}</li>" for _ in range(n))
    return f"<ul>{items}</ul>", "ul", None


@st.composite
def ordered_list_element(draw):
    """Generate an ordered list with 1-4 items."""
    n = draw(st.integers(min_value=1, max_value=4))
    items = "".join(f"<li>{draw(_text)}</li>" for _ in range(n))
    return f"<ol>{items}</ol>", "ol", None


@st.composite
def table_element(draw):
    """Generate a simple HTML table with a header row and 1-3 data rows."""
    cols = draw(st.integers(min_value=1, max_value=3))
    header = "<tr>" + "".join(f"<th>{draw(_text)}</th>" for _ in range(cols)) + "</tr>"
    num_rows = draw(st.integers(min_value=1, max_value=3))
    rows = "".join(
        "<tr>" + "".join(f"<td>{draw(_text)}</td>" for _ in range(cols)) + "</tr>"
        for _ in range(num_rows)
    )
    return f"<table><thead>{header}</thead><tbody>{rows}</tbody></table>", "table", None


@st.composite
def bold_element(draw):
    """Generate a bold/strong element."""
    text = draw(_text)
    tag = draw(st.sampled_from(["strong", "b"]))
    return f"<p><{tag}>{text}</{tag}></p>", "bold", None


@st.composite
def italic_element(draw):
    """Generate an italic/em element."""
    text = draw(_text)
    tag = draw(st.sampled_from(["em", "i"]))
    return f"<p><{tag}>{text}</{tag}></p>", "italic", None


@st.composite
def image_element(draw):
    """Generate an image element."""
    alt = draw(_text)
    return f'<img src="https://example.com/img.png" alt="{alt}" />', "image", None


# All element generators
_element_strategies = [
    heading_element(),
    code_block_element(),
    unordered_list_element(),
    ordered_list_element(),
    table_element(),
    bold_element(),
    italic_element(),
    image_element(),
]


@st.composite
def html_with_semantic_elements(draw):
    """Generate HTML with a random combination of semantic elements.

    Returns (html_string, set_of_element_types, metadata_dict) where
    metadata_dict maps element types to extra info (e.g. heading level).
    """
    # Pick at least 1 element type, up to all of them
    num_elements = draw(st.integers(min_value=1, max_value=len(_element_strategies)))
    chosen_indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=len(_element_strategies) - 1),
            min_size=num_elements,
            max_size=num_elements,
            unique=True,
        )
    )

    snippets = []
    element_types = set()
    metadata = {}

    for idx in chosen_indices:
        html_snippet, etype, extra = draw(_element_strategies[idx])
        snippets.append(html_snippet)
        element_types.add(etype)
        if etype == "heading" and extra is not None:
            metadata.setdefault("heading_levels", set()).add(extra)

    body = "\n".join(snippets)
    full_html = f"<div>{body}</div>"
    return full_html, element_types, metadata


@given(data=html_with_semantic_elements())
@settings(max_examples=100)
def test_markdown_conversion_preserves_semantic_structure(data):
    """Property 2: Markdown conversion preserves semantic structure.

    **Validates: Requirements 2.1, 2.3**

    For any HTML article content containing semantic elements (headings,
    code blocks, lists, tables, bold, italic, images), the converted
    Markdown output should contain the corresponding Markdown syntax markers.
    """
    html_str, element_types, metadata = data
    soup = BeautifulSoup(html_str, "html.parser")
    md = convert_to_markdown(soup)

    for etype in element_types:
        if etype == "heading":
            # Each heading level should produce '#' markers
            for level in metadata.get("heading_levels", set()):
                marker = "#" * level
                assert marker in md, (
                    f"Expected heading marker '{marker}' for h{level} "
                    f"not found in Markdown output:\n{md}"
                )

        elif etype == "code":
            # Code blocks should produce triple backticks or indented code
            has_backticks = "```" in md
            # Check for indented code (4 spaces)
            has_indented = any(
                line.startswith("    ") and line.strip()
                for line in md.splitlines()
            )
            assert has_backticks or has_indented, (
                f"Expected code block markers (``` or indented) "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "ul":
            # Unordered list items should use * or - markers
            assert any(
                line.lstrip().startswith("*") or line.lstrip().startswith("-")
                for line in md.splitlines()
            ), (
                f"Expected unordered list markers (* or -) "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "ol":
            # Ordered list items should use numbered markers like "1."
            assert any(
                line.lstrip()[:1].isdigit() and "." in line.lstrip()[:4]
                for line in md.splitlines()
            ), (
                f"Expected ordered list markers (e.g. '1.') "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "table":
            # Tables should produce | markers
            assert "|" in md, (
                f"Expected table marker '|' "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "bold":
            # Bold text should produce ** markers
            assert "**" in md, (
                f"Expected bold marker '**' "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "italic":
            # Italic text should produce * or _ markers
            assert "*" in md or "_" in md, (
                f"Expected italic marker ('*' or '_') "
                f"not found in Markdown output:\n{md}"
            )

        elif etype == "image":
            # Images should produce ![ markers
            assert "![" in md, (
                f"Expected image marker '![' "
                f"not found in Markdown output:\n{md}"
            )
