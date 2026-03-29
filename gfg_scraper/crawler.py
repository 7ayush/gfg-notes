"""BFS crawler module that orchestrates the scraping pipeline."""

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
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

_MANIFEST_FILE = ".scraper_manifest.json"


def _load_manifest(output_dir: str) -> dict:
    """Load manifest from a previous run.

    Returns dict with keys: "pages" (url -> {filepath, children, depth, parent_dir, order})
    """
    path = os.path.join(output_dir, _MANIFEST_FILE)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Handle old format (flat url->filepath dict)
        if data and isinstance(next(iter(data.values()), None), str):
            return {"pages": {url: {"filepath": fp, "children": []} for url, fp in data.items()}}
        return data
    return {"pages": {}}


def _save_manifest(output_dir: str, manifest: dict) -> None:
    """Persist manifest for resume support."""
    path = os.path.join(output_dir, _MANIFEST_FILE)
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


def _process_page(url, depth, parent_dir, discovery_order, config):
    """Fetch, extract, convert, and save a single page. Thread-safe."""
    html = fetch_page(url, config)
    if html is None:
        logger.error("Failed to fetch %s, skipping.", url)
        return None
    try:
        article = extract_article_content(html, url)
        if article is None:
            logger.warning("No article content at %s, skipping.", url)
            return None
        child_links = extract_internal_links(article, url)
        file_path = build_file_path(url, parent_dir, discovery_order)
        download_images(article, config.output_dir, file_path, config)
        markdown = convert_to_markdown(article)
        save_markdown(file_path, markdown)
    except Exception:
        logger.exception("Error processing %s, skipping.", url)
        return None
    return url, file_path, child_links


def _rebuild_queue_from_manifest(manifest, start_url, config):
    """Rebuild BFS queue from manifest, returning only unprocessed URLs."""
    pages = manifest["pages"]
    done_urls = set(pages.keys())

    queue = deque()
    visited = set(done_urls)
    visited.add(start_url)

    # BFS through already-done pages using stored children (no network calls)
    bfs = deque()
    bfs.append((start_url, 0, config.output_dir, 1))

    while bfs:
        url, depth, parent_dir, order = bfs.popleft()
        if depth >= config.max_depth:
            continue

        info = pages.get(url)
        if not info:
            # Not yet scraped — add to work queue
            if url not in done_urls:
                queue.append((url, depth, parent_dir, order))
            continue

        fp = info["filepath"]
        child_parent_dir = os.path.splitext(fp)[0]
        child_order = 0
        for child_url in info.get("children", []):
            normalized = normalize_url(child_url)
            if normalized not in visited:
                visited.add(normalized)
                child_order += 1
                if normalized in done_urls:
                    bfs.append((normalized, depth + 1, child_parent_dir, child_order))
                else:
                    queue.append((normalized, depth + 1, child_parent_dir, child_order))

    return queue, visited


def crawl(config):
    """BFS crawl with resume support and parallel workers."""
    start_url = normalize_url(config.start_url)
    manifest = _load_manifest(config.output_dir)
    pages = manifest["pages"]
    already_done = set(pages.keys())

    # Build url_to_filepath for the rewriter
    url_to_filepath = {url: info["filepath"] for url, info in pages.items()
                       if isinstance(info, dict) and "filepath" in info}

    if already_done and start_url in already_done:
        # Resuming same start URL — rebuild queue from manifest
        print(f"Resuming: {len(already_done)} pages already scraped.")
        queue, visited = _rebuild_queue_from_manifest(manifest, start_url, config)
        print(f"Queue rebuilt: {len(queue)} new pages to process.")
    else:
        # New start URL or fresh run — just use manifest as visited set
        queue = deque()
        queue.append((start_url, 0, config.output_dir, 1))
        visited = set(already_done)
        visited.add(start_url)
        if already_done:
            print(f"New start URL. {len(already_done)} pages from previous runs will be skipped.")

    pages_scraped = len(already_done)
    new_pages_count = 0
    new_url_to_filepath: dict[str, str] = {}
    manifest_counter = 0
    num_workers = max(1, config.workers)

    while queue:
        if config.max_pages > 0 and pages_scraped >= config.max_pages:
            print(f"Reached max pages limit ({config.max_pages}). Stopping.")
            break

        # Collect batch
        batch = []
        while queue and len(batch) < num_workers:
            entry = queue.popleft()
            if entry[0] not in already_done:
                batch.append(entry)
        if not batch:
            continue

        # Process in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = {
                pool.submit(_process_page, url, depth, pdir, order, config): (url, depth, pdir, order)
                for url, depth, pdir, order in batch
            }
            for future in as_completed(futures):
                url, depth, parent_dir, order = futures[future]
                result = future.result()
                if result is None:
                    continue

                ret_url, file_path, child_links = result
                url_to_filepath[ret_url] = file_path
                new_url_to_filepath[ret_url] = file_path
                normalized_children = [normalize_url(c) for c in child_links]
                manifest["pages"][ret_url] = {
                    "filepath": file_path,
                    "children": normalized_children,
                }
                already_done.add(ret_url)
                pages_scraped += 1
                new_pages_count += 1
                manifest_counter += 1

                print(f"[{pages_scraped}] Saved: {file_path} (depth {depth}, queue: {len(queue)}, visited: {len(visited)})")

                if depth < config.max_depth:
                    child_parent_dir = os.path.splitext(file_path)[0]
                    child_order = 0
                    for link in normalized_children:
                        if link not in visited:
                            visited.add(link)
                            child_order += 1
                            queue.append((link, depth + 1, child_parent_dir, child_order))

                if manifest_counter >= 50:
                    _save_manifest(config.output_dir, manifest)
                    manifest_counter = 0

    _save_manifest(config.output_dir, manifest)
    return CrawlResult(pages_scraped, config.output_dir), new_url_to_filepath
