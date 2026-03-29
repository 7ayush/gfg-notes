"""BFS crawler module that orchestrates the scraping pipeline."""

from collections import deque
import logging
import os

from gfg_scraper.config import CrawlResult, ScraperConfig
from gfg_scraper.fetcher import fetch_page
from gfg_scraper.extractor import extract_article_content
from gfg_scraper.links import extract_internal_links, normalize_url
from gfg_scraper.converter import convert_to_markdown
from gfg_scraper.images import download_images
from gfg_scraper.writer import build_file_path, save_markdown

logger = logging.getLogger(__name__)


def crawl(config: ScraperConfig) -> tuple[CrawlResult, dict[str, str]]:
    """
    BFS crawl starting from config.start_url.
    Coordinates fetching, extraction, conversion, writing, and link discovery.

    Returns a tuple of (CrawlResult summary, url_to_filepath mapping).
    The mapping is needed by the link rewriter in the post-processing pass.
    """
    start_url = normalize_url(config.start_url)

    # BFS queue entries: (url, depth, parent_dir, discovery_order)
    queue: deque[tuple[str, int, str, int]] = deque()
    queue.append((start_url, 0, config.output_dir, 1))

    visited: set[str] = {start_url}
    url_to_filepath: dict[str, str] = {}
    pages_scraped = 0

    while queue:
        # Check max pages limit
        if config.max_pages > 0 and pages_scraped >= config.max_pages:
            print(f"Reached max pages limit ({config.max_pages}). Stopping crawl.")
            break

        url, depth, parent_dir, discovery_order = queue.popleft()

        print(f"[{pages_scraped + 1}] Fetching: {url} (depth {depth}, queue: {len(queue)}, visited: {len(visited)})")

        # --- Fetch ---
        html = fetch_page(url, config)
        if html is None:
            logger.error("Failed to fetch %s, skipping.", url)
            continue

        # --- Extract / Convert / Save (wrapped for resilience) ---
        try:
            article = extract_article_content(html, url)
            if article is None:
                logger.warning("No article content at %s, skipping.", url)
                continue

            # Discover internal links *before* conversion
            child_links = extract_internal_links(article, url)

            # Build file path (needed for relative image paths)
            file_path = build_file_path(url, parent_dir, discovery_order)

            # Download images and rewrite src to local paths
            download_images(article, config.output_dir, file_path, config)

            # Convert to Markdown
            markdown = convert_to_markdown(article)

            # Save
            save_markdown(file_path, markdown)
        except Exception:
            logger.exception("Error processing %s, skipping.", url)
            continue

        # Track the mapping and bump counter
        url_to_filepath[url] = file_path
        pages_scraped += 1

        print(f"Saved: {file_path}")

        # --- Enqueue children (only if below max depth) ---
        if depth < config.max_depth:
            # Child pages live in a subdirectory named after the current file
            # (strip the .md extension to create the subdirectory path)
            child_parent_dir = os.path.splitext(file_path)[0]
            child_order = 0
            for link in child_links:
                normalized = normalize_url(link)
                if normalized not in visited:
                    visited.add(normalized)
                    child_order += 1
                    queue.append((normalized, depth + 1, child_parent_dir, child_order))

    return CrawlResult(pages_scraped, config.output_dir), url_to_filepath
