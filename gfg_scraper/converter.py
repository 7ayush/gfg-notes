"""Markdown conversion module."""

import re

from bs4 import BeautifulSoup
from markdownify import markdownify


def convert_to_markdown(article_soup: BeautifulSoup) -> str:
    """
    Convert article HTML to clean Markdown using markdownify.
    Preserves headings, code blocks, lists, tables, bold/italic, images.
    """
    html = str(article_soup)
    md = markdownify(
        html,
        heading_style="ATX",
        code_language="",
        convert=["h1", "h2", "h3", "h4", "h5", "h6",
                 "p", "a", "img",
                 "strong", "b", "em", "i",
                 "pre", "code",
                 "ul", "ol", "li",
                 "table", "thead", "tbody", "tr", "th", "td",
                 "br", "hr", "blockquote", "div", "span", "sup", "sub"],
        strip=None,
    )
    # Collapse runs of 3+ blank lines into 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()
