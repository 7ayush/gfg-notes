"""Unit tests for the crawler module.

Tests BFS ordering, depth limiting, visited set deduplication,
error handling resilience, and CrawlResult correctness.

Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 9.1, 9.2, 9.3
"""

import os
from unittest.mock import patch, call

from bs4 import BeautifulSoup

from gfg_scraper.config import ScraperConfig
from gfg_scraper.crawler import crawl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

START = "https://www.geeksforgeeks.org/start"
CHILD_A = "https://www.geeksforgeeks.org/child-a"
CHILD_B = "https://www.geeksforgeeks.org/child-b"
GRANDCHILD_A1 = "https://www.geeksforgeeks.org/grandchild-a1"
GRANDCHILD_B1 = "https://www.geeksforgeeks.org/grandchild-b1"


def _html(links: list[str]) -> str:
    anchors = "".join(f'<a href="{u}">link</a>' for u in links)
    return f"<html><body><article><p>Content</p>{anchors}</article></body></html>"


def _soup(links: list[str]) -> BeautifulSoup:
    anchors = "".join(f'<a href="{u}">link</a>' for u in links)
    return BeautifulSoup(f"<article><p>Content</p>{anchors}</article>", "html.parser")


def _config(tmp_path, max_depth=2):
    return ScraperConfig(
        start_url=START,
        max_depth=max_depth,
        output_dir=str(tmp_path),
        polite_delay=0,
        request_timeout=10.0,
    )


# Page graph: START -> [CHILD_A, CHILD_B], each child -> [grandchild]
PAGES = {
    START: [CHILD_A, CHILD_B],
    CHILD_A: [GRANDCHILD_A1],
    CHILD_B: [GRANDCHILD_B1],
    GRANDCHILD_A1: [],
    GRANDCHILD_B1: [],
}


def _run_crawl(config, pages, fetch_side_effect=None):
    """Run crawl with standard mocks. Returns (result, url_to_filepath, fetch_calls)."""
    fetch_calls = []
    file_counter = [0]

    def mock_fetch(url, cfg):
        fetch_calls.append(url)
        if fetch_side_effect and url in fetch_side_effect:
            return fetch_side_effect[url]
        if url in pages:
            return _html(pages[url])
        return _html([])

    def mock_extract(html, url):
        return _soup(pages.get(url, []))

    def mock_extract_links(article_soup, base_url):
        return pages.get(base_url, [])

    def mock_convert(article_soup):
        return "# Mock"

    def mock_build_path(url, parent_dir, discovery_order):
        file_counter[0] += 1
        return os.path.join(parent_dir, f"{file_counter[0]:02d}_page.md")

    def mock_save(file_path, content):
        pass

    with patch("gfg_scraper.crawler.fetch_page", side_effect=mock_fetch), \
         patch("gfg_scraper.crawler.extract_article_content", side_effect=mock_extract), \
         patch("gfg_scraper.crawler.extract_internal_links", side_effect=mock_extract_links), \
         patch("gfg_scraper.crawler.convert_to_markdown", side_effect=mock_convert), \
         patch("gfg_scraper.crawler.build_file_path", side_effect=mock_build_path), \
         patch("gfg_scraper.crawler.save_markdown", side_effect=mock_save), \
         patch("gfg_scraper.crawler.download_images"), \
         patch("gfg_scraper.crawler._load_manifest", return_value={"pages": {}}), \
         patch("gfg_scraper.crawler._save_manifest"):
        result, url_to_filepath = crawl(config)

    return result, url_to_filepath, fetch_calls


# ---------------------------------------------------------------------------
# Test 1: BFS order of page processing
# ---------------------------------------------------------------------------

def test_bfs_order(tmp_path):
    """Start page has 2 children; verify they're processed breadth-first.

    Requirements: 4.1, 4.2
    """
    config = _config(tmp_path, max_depth=2)
    result, url_to_filepath, fetch_calls = _run_crawl(config, PAGES)

    # BFS order: start first, then both children before any grandchild
    assert fetch_calls[0] == START
    # Children should appear before grandchildren
    children_idx = {fetch_calls.index(CHILD_A), fetch_calls.index(CHILD_B)}
    grandchildren_idx = {fetch_calls.index(GRANDCHILD_A1), fetch_calls.index(GRANDCHILD_B1)}
    assert max(children_idx) < min(grandchildren_idx), (
        "Children must be processed before grandchildren in BFS"
    )


# ---------------------------------------------------------------------------
# Test 2: Depth limiting stops link following at MAX_DEPTH
# ---------------------------------------------------------------------------

def test_depth_limiting(tmp_path):
    """max_depth=1: children are saved but grandchildren are not.

    Requirements: 4.3, 4.4
    """
    config = _config(tmp_path, max_depth=1)
    result, url_to_filepath, fetch_calls = _run_crawl(config, PAGES)

    # Start (depth 0) and children (depth 1) should be fetched
    assert START in fetch_calls
    assert CHILD_A in fetch_calls
    assert CHILD_B in fetch_calls

    # Grandchildren (depth 2) should NOT be fetched
    assert GRANDCHILD_A1 not in fetch_calls
    assert GRANDCHILD_B1 not in fetch_calls

    # Children should be saved
    assert CHILD_A in url_to_filepath
    assert CHILD_B in url_to_filepath


# ---------------------------------------------------------------------------
# Test 3: Visited set prevents duplicate fetches
# ---------------------------------------------------------------------------

def test_visited_set_prevents_duplicates(tmp_path):
    """Two pages link to the same child; verify it's fetched only once.

    Requirements: 5.1, 5.2, 5.3
    """
    shared_child = "https://www.geeksforgeeks.org/shared"
    pages = {
        START: [CHILD_A, CHILD_B],
        CHILD_A: [shared_child],
        CHILD_B: [shared_child],
        shared_child: [],
    }
    config = _config(tmp_path, max_depth=2)
    result, url_to_filepath, fetch_calls = _run_crawl(config, pages)

    # shared_child should appear exactly once in fetch_calls
    assert fetch_calls.count(shared_child) == 1


# ---------------------------------------------------------------------------
# Test 4: Fetch failure – crawl continues with other URLs
# ---------------------------------------------------------------------------

def test_fetch_failure_continues_crawl(tmp_path):
    """Mock fetch_page to return None for CHILD_A. Crawl should continue.

    Requirements: 9.1, 9.2
    """
    config = _config(tmp_path, max_depth=1)
    # CHILD_A fetch fails, CHILD_B succeeds
    fetch_overrides = {CHILD_A: None}
    result, url_to_filepath, fetch_calls = _run_crawl(config, PAGES, fetch_side_effect=fetch_overrides)

    # Both children were attempted
    assert CHILD_A in fetch_calls
    assert CHILD_B in fetch_calls

    # CHILD_A should NOT be in saved pages (fetch failed)
    assert CHILD_A not in url_to_filepath
    # CHILD_B should be saved
    assert CHILD_B in url_to_filepath
    # Start page should be saved
    assert START in url_to_filepath


# ---------------------------------------------------------------------------
# Test 5: Extract failure – crawl continues
# ---------------------------------------------------------------------------

def test_extract_failure_continues_crawl(tmp_path):
    """Mock extract_article_content to return None for CHILD_A. Crawl continues.

    Requirements: 9.3
    """
    file_counter = [0]

    def mock_fetch(url, cfg):
        return _html(PAGES.get(url, []))

    def mock_extract(html, url):
        if url == CHILD_A:
            return None  # extraction fails for CHILD_A
        return _soup(PAGES.get(url, []))

    def mock_extract_links(article_soup, base_url):
        return PAGES.get(base_url, [])

    def mock_convert(article_soup):
        return "# Mock"

    def mock_build_path(url, parent_dir, discovery_order):
        file_counter[0] += 1
        return os.path.join(parent_dir, f"{file_counter[0]:02d}_page.md")

    def mock_save(file_path, content):
        pass

    config = _config(tmp_path, max_depth=1)

    with patch("gfg_scraper.crawler.fetch_page", side_effect=mock_fetch), \
         patch("gfg_scraper.crawler.extract_article_content", side_effect=mock_extract), \
         patch("gfg_scraper.crawler.extract_internal_links", side_effect=mock_extract_links), \
         patch("gfg_scraper.crawler.convert_to_markdown", side_effect=mock_convert), \
         patch("gfg_scraper.crawler.build_file_path", side_effect=mock_build_path), \
         patch("gfg_scraper.crawler.save_markdown", side_effect=mock_save), \
         patch("gfg_scraper.crawler.download_images"), \
         patch("gfg_scraper.crawler._load_manifest", return_value={"pages": {}}), \
         patch("gfg_scraper.crawler._save_manifest"):
        result, url_to_filepath = crawl(config)

    # CHILD_A should NOT be saved (extract returned None)
    assert CHILD_A not in url_to_filepath
    # CHILD_B should be saved
    assert CHILD_B in url_to_filepath
    # Start should be saved
    assert START in url_to_filepath


# ---------------------------------------------------------------------------
# Test 6: Start URL is treated as depth 0
# ---------------------------------------------------------------------------

def test_start_url_is_depth_zero(tmp_path):
    """With max_depth=0, only the start URL is saved; no children are followed.

    Requirements: 4.4
    """
    config = _config(tmp_path, max_depth=0)
    result, url_to_filepath, fetch_calls = _run_crawl(config, PAGES)

    # Only start URL should be fetched and saved
    assert fetch_calls == [START]
    assert START in url_to_filepath
    assert len(url_to_filepath) == 1


# ---------------------------------------------------------------------------
# Test 7: Pages scraped count matches actual saved pages
# ---------------------------------------------------------------------------

def test_pages_scraped_count(tmp_path):
    """CrawlResult.pages_scraped matches the number of actually saved pages.

    Requirements: 4.1
    """
    config = _config(tmp_path, max_depth=2)
    result, url_to_filepath, fetch_calls = _run_crawl(config, PAGES)

    assert result.pages_scraped == len(url_to_filepath)
    # With full graph and depth=2, all 5 pages should be saved
    assert result.pages_scraped == 5
    assert result.output_dir == str(tmp_path)
