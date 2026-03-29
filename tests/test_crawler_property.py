"""Property-based tests for the crawler module.

Feature: gfg-web-scraper, Property 5: Depth limiting prevents link following at MAX_DEPTH
"""

import os
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from gfg_scraper.config import ScraperConfig
from gfg_scraper.crawler import crawl


# ---------------------------------------------------------------------------
# Strategies for Property 5 – depth limiting
# ---------------------------------------------------------------------------

@st.composite
def page_graph(draw):
    """Generate a mock page graph with a configurable max_depth (0-3).

    Returns (max_depth, pages_dict) where pages_dict maps URL -> list of child URLs.
    Each page has 1-3 child links. The graph is a tree rooted at the start URL,
    extending one level beyond max_depth so we can verify those pages are NOT visited.
    """
    max_depth = draw(st.integers(min_value=0, max_value=3))

    pages: dict[str, list[str]] = {}
    counter = 0

    def build_level(depth: int, parent_url: str):
        nonlocal counter
        num_children = draw(st.integers(min_value=1, max_value=3))
        children = []
        for _ in range(num_children):
            counter += 1
            child_url = f"https://www.geeksforgeeks.org/page-{counter}"
            children.append(child_url)
        pages[parent_url] = children

        # Build one more level beyond max_depth so we have "beyond" pages to check
        if depth < max_depth + 1:
            for child in children:
                if child not in pages:
                    build_level(depth + 1, child)

    start_url = "https://www.geeksforgeeks.org/start"
    build_level(0, start_url)

    return max_depth, start_url, pages


def _make_html(links: list[str]) -> str:
    """Build a minimal HTML page with an <article> containing links."""
    anchors = "".join(f'<a href="{u}">link</a>' for u in links)
    return f"<html><body><article><p>Content</p>{anchors}</article></body></html>"


def _make_soup(links: list[str]) -> BeautifulSoup:
    """Build a BeautifulSoup article tag containing the given links."""
    anchors = "".join(f'<a href="{u}">link</a>' for u in links)
    html = f"<article><p>Content</p>{anchors}</article>"
    return BeautifulSoup(html, "html.parser")


@given(data=page_graph())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_depth_limiting_prevents_link_following_at_max_depth(data, tmp_path):
    """Property 5: Depth limiting prevents link following at MAX_DEPTH.

    **Validates: Requirements 4.3**

    For any MAX_DEPTH value and any page discovered at depth equal to MAX_DEPTH,
    the crawler should save that page's content but should not enqueue any of its
    child links for processing.
    """
    max_depth, start_url, pages = data

    config = ScraperConfig(
        start_url=start_url,
        max_depth=max_depth,
        output_dir=str(tmp_path),
        polite_delay=0,
        request_timeout=10.0,
    )

    # Track which URLs get saved
    saved_files: dict[str, str] = {}
    file_counter = 0

    def mock_fetch_page(url, cfg):
        if url in pages:
            return _make_html(pages[url])
        # Leaf pages with no children entry still return valid HTML
        return _make_html([])

    def mock_extract_article_content(html, url):
        if url in pages:
            return _make_soup(pages[url])
        return _make_soup([])

    def mock_extract_internal_links(article_soup, base_url):
        return pages.get(base_url, [])

    def mock_convert_to_markdown(article_soup):
        return "# Mock content"

    def mock_build_file_path(url, parent_dir, discovery_order):
        nonlocal file_counter
        file_counter += 1
        fp = os.path.join(parent_dir, f"{file_counter:02d}_page.md")
        return fp

    def mock_save_markdown(file_path, content):
        pass

    with patch("gfg_scraper.crawler.fetch_page", side_effect=mock_fetch_page), \
         patch("gfg_scraper.crawler.extract_article_content", side_effect=mock_extract_article_content), \
         patch("gfg_scraper.crawler.extract_internal_links", side_effect=mock_extract_internal_links), \
         patch("gfg_scraper.crawler.convert_to_markdown", side_effect=mock_convert_to_markdown), \
         patch("gfg_scraper.crawler.build_file_path", side_effect=mock_build_file_path), \
         patch("gfg_scraper.crawler.save_markdown", side_effect=mock_save_markdown):

        result, url_to_filepath = crawl(config)

    # Compute which pages are at each depth via BFS
    depth_map: dict[str, int] = {start_url: 0}
    bfs_queue = [start_url]
    while bfs_queue:
        current = bfs_queue.pop(0)
        current_depth = depth_map[current]
        if current_depth < max_depth:
            for child in pages.get(current, []):
                if child not in depth_map:
                    depth_map[child] = current_depth + 1
                    bfs_queue.append(child)

    # Pages at max_depth should be saved (present in url_to_filepath)
    pages_at_max_depth = [u for u, d in depth_map.items() if d == max_depth]
    for url in pages_at_max_depth:
        assert url in url_to_filepath, (
            f"Page at max_depth ({max_depth}) should be saved: {url}"
        )

    # Child links of pages at max_depth should NOT be in url_to_filepath
    for url in pages_at_max_depth:
        for child in pages.get(url, []):
            if child not in depth_map or depth_map[child] > max_depth:
                assert child not in url_to_filepath, (
                    f"Child link of page at max_depth should NOT be saved: {child} "
                    f"(child of {url} at depth {max_depth})"
                )


# ---------------------------------------------------------------------------
# Strategies for Property 6 – cycle prevention
# ---------------------------------------------------------------------------

@st.composite
def cyclic_page_graph(draw):
    """Generate a mock page graph WITH CYCLES.

    Returns (pages_dict, start_url) where pages_dict maps URL -> list of child URLs.
    Pages link to each other creating cycles (back-links to already-visited pages).
    Uses a fixed high max_depth (10) so cycle prevention is what stops the crawl,
    not depth limiting.
    """
    num_pages = draw(st.integers(min_value=3, max_value=8))
    urls = [f"https://www.geeksforgeeks.org/page-{i}" for i in range(num_pages)]
    start_url = urls[0]

    pages: dict[str, list[str]] = {}
    for url in urls:
        # Each page links to 1-4 other pages (including potential back-links)
        num_links = draw(st.integers(min_value=1, max_value=min(4, num_pages)))
        targets = draw(
            st.lists(
                st.sampled_from(urls),
                min_size=num_links,
                max_size=num_links,
            )
        )
        pages[url] = targets

    return pages, start_url


@given(data=cyclic_page_graph())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_cycle_prevention_fetches_each_url_at_most_once(data, tmp_path):
    """Property 6: Cycle prevention ensures each unique URL is fetched at most once.

    **Validates: Requirements 5.1, 5.2**

    For any set of pages forming a link graph (including cycles), the crawler
    should fetch each unique normalized URL exactly once, regardless of how many
    times it is linked from different pages.

    Tag: Feature: gfg-web-scraper, Property 6: Cycle prevention ensures each unique URL is fetched at most once
    """
    pages, start_url = data

    config = ScraperConfig(
        start_url=start_url,
        max_depth=10,  # High enough so depth doesn't limit; cycles do
        output_dir=str(tmp_path),
        polite_delay=0,
        request_timeout=10.0,
    )

    # Track how many times each URL is fetched
    fetch_counts: dict[str, int] = {}
    file_counter = 0

    def mock_fetch_page(url, cfg):
        fetch_counts[url] = fetch_counts.get(url, 0) + 1
        return _make_html(pages.get(url, []))

    def mock_extract_article_content(html, url):
        return _make_soup(pages.get(url, []))

    def mock_extract_internal_links(article_soup, base_url):
        return pages.get(base_url, [])

    def mock_convert_to_markdown(article_soup):
        return "# Mock content"

    def mock_build_file_path(url, parent_dir, discovery_order):
        nonlocal file_counter
        file_counter += 1
        fp = os.path.join(parent_dir, f"{file_counter:02d}_page.md")
        return fp

    def mock_save_markdown(file_path, content):
        pass

    with patch("gfg_scraper.crawler.fetch_page", side_effect=mock_fetch_page), \
         patch("gfg_scraper.crawler.extract_article_content", side_effect=mock_extract_article_content), \
         patch("gfg_scraper.crawler.extract_internal_links", side_effect=mock_extract_internal_links), \
         patch("gfg_scraper.crawler.convert_to_markdown", side_effect=mock_convert_to_markdown), \
         patch("gfg_scraper.crawler.build_file_path", side_effect=mock_build_file_path), \
         patch("gfg_scraper.crawler.save_markdown", side_effect=mock_save_markdown):

        result, url_to_filepath = crawl(config)

    # Assert each unique URL was fetched at most once
    for url, count in fetch_counts.items():
        assert count == 1, (
            f"URL {url} was fetched {count} times, expected exactly once. "
            f"Graph: {pages}"
        )

    # Also verify that all reachable URLs were actually fetched
    # (BFS from start_url through the graph)
    reachable: set[str] = set()
    bfs_queue = [start_url]
    reachable.add(start_url)
    while bfs_queue:
        current = bfs_queue.pop(0)
        for child in pages.get(current, []):
            if child not in reachable:
                reachable.add(child)
                bfs_queue.append(child)

    assert set(fetch_counts.keys()) == reachable, (
        f"Fetched URLs {set(fetch_counts.keys())} != reachable URLs {reachable}"
    )
