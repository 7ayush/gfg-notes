# Implementation Plan: GfG Web Scraper

## Overview

Incrementally build the GfG web scraper in Python, starting with core data models and utility modules, then composing them into the BFS crawler, and finishing with CLI wiring and post-processing link rewriting. Each task builds on the previous ones. Property-based tests use `hypothesis`; unit tests use `pytest`.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create the project directory with the following modules: `cli.py`, `fetcher.py`, `extractor.py`, `links.py`, `converter.py`, `writer.py`, `rewriter.py`, `crawler.py`
  - Create `requirements.txt` with dependencies: `requests`, `beautifulsoup4`, `markdownify`, `hypothesis`, `pytest`, `responses`
  - Define `ScraperConfig` dataclass in a `config.py` module with fields: `start_url`, `max_depth=2`, `output_dir="output"`, `polite_delay=2.0`, `request_timeout=30.0`
  - Define `PageRecord` and `CrawlResult` dataclasses in `config.py`
  - _Requirements: 4.1, 4.2, 8.3, 9.4, 10.2_

- [ ] 2. Implement URL normalization and link filtering (`links.py`)
  - [x] 2.1 Implement `normalize_url(url)` to strip query parameters and fragment identifiers
    - Use `urllib.parse` to parse, clear query/fragment, and reassemble the URL
    - _Requirements: 3.4_

  - [x] 2.2 Write property test for URL normalization (Property 4)
    - **Property 4: URL normalization is idempotent and strips query/fragment**
    - Use `hypothesis` to generate URLs with random query params and fragments
    - Assert `normalize(normalize(url)) == normalize(url)` and that result contains no `?` or `#`
    - **Validates: Requirements 3.4**

  - [x] 2.3 Implement `extract_internal_links(article_soup, base_url)` to extract, filter, and normalize internal GfG links
    - Accept only HTTP/HTTPS links with domain `geeksforgeeks.org`
    - Reject anchor-only, `mailto:`, `javascript:`, and external links
    - Return deduplicated list preserving discovery order
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.4 Write property test for link filtering (Property 3)
    - **Property 3: Link filtering only passes valid internal GfG links**
    - Generate random URLs with various schemes, domains, fragments
    - Assert only HTTP(S) `geeksforgeeks.org` links pass the filter
    - **Validates: Requirements 3.2, 3.3**

  - [x] 2.5 Write unit tests for `links.py`
    - Test normalization of URLs with query params, fragments, both, and neither
    - Test filtering with external domains, anchor-only links, mailto links
    - Test deduplication and discovery order preservation
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 3. Implement content extraction (`extractor.py`)
  - [x] 3.1 Implement `extract_article_content(html, url)` to isolate article body
    - Target `<article>` tag or main content `<div>` using BeautifulSoup
    - Strip `<nav>`, `<aside>`, `<footer>`, `<header>`, and ad-class elements from extracted content
    - Return `None` and log warning if article structure not found
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Write property test for content extraction (Property 1)
    - **Property 1: Article content extraction isolates the article body**
    - Generate HTML with random article content plus random unwanted elements (nav, aside, footer, header, ad divs)
    - Assert returned content contains no unwanted tags
    - **Validates: Requirements 1.1, 1.2**

  - [x] 3.3 Write unit tests for `extractor.py`
    - Test extraction from HTML with `<article>` tag
    - Test fallback to main content `<div>` when no `<article>` tag
    - Test `None` return and warning log when no article structure found
    - Test stripping of sidebar, nav, footer, header, ad elements
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 4. Implement Markdown conversion (`converter.py`)
  - [x] 4.1 Implement `convert_to_markdown(article_soup)` using `markdownify`
    - Preserve headings, code blocks, lists, tables, bold/italic, images
    - Return clean Markdown string
    - _Requirements: 2.1, 2.3_

  - [x] 4.2 Write property test for Markdown conversion (Property 2)
    - **Property 2: Markdown conversion preserves semantic structure**
    - Generate HTML with random combinations of semantic elements (h1-h6, code, lists, tables, bold, italic, images)
    - Assert corresponding Markdown syntax markers are present in output
    - **Validates: Requirements 2.1, 2.3**

  - [x] 4.3 Write unit tests for `converter.py`
    - Test conversion of headings, code blocks, lists, tables, bold/italic, images
    - Test handling of empty content
    - _Requirements: 2.1, 2.3_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement file writer (`writer.py`)
  - [x] 6.1 Implement `build_file_path(url, parent_dir, discovery_order)` for filename generation
    - Derive filename from URL path slug, replacing hyphens and special characters with underscores
    - Prepend zero-padded discovery order number (e.g., `01_Introduction.md`)
    - Create parent directories with `os.makedirs(exist_ok=True)`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 6.2 Implement `save_markdown(file_path, content)` to write Markdown to disk
    - _Requirements: 2.2_

  - [x] 6.3 Write property test for filename generation (Property 8)
    - **Property 8: Filename generation produces valid numbered slugs with .md extension**
    - Generate random URL slugs and discovery order numbers
    - Assert filename starts with zero-padded number, contains only alphanumeric/underscores in slug, ends with `.md`
    - **Validates: Requirements 2.2, 7.2, 7.3**

  - [x] 6.4 Write unit tests for `writer.py`
    - Test filename derivation from various URL slugs
    - Test zero-padding for single and multi-digit discovery orders
    - Test directory creation
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 7. Implement HTTP fetcher (`fetcher.py`)
  - [x] 7.1 Implement `fetch_page(url, config)` with polite behavior
    - Set browser User-Agent header (not default `requests` UA)
    - Apply `config.polite_delay` sleep before each request
    - Set `config.request_timeout` on the request
    - Return HTML string on success, `None` on error
    - Log errors for network failures, timeouts, and non-2xx status codes
    - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 9.4_

  - [x] 7.2 Write unit tests for `fetcher.py`
    - Mock HTTP responses using `responses` library
    - Test successful fetch returns HTML
    - Test non-2xx status code returns `None` and logs error
    - Test network timeout returns `None` and logs error
    - Test User-Agent header is set to browser string
    - Test polite delay is applied
    - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 9.4_

- [ ] 8. Implement BFS crawler (`crawler.py`)
  - [x] 8.1 Implement `crawl(config)` with BFS queue and visited set
    - Seed queue with `(start_url, depth=0)`
    - For each URL: fetch, extract, discover links, convert, save
    - Maintain `visited_set` — add URL before fetching
    - Enqueue child links only if `depth < max_depth` and URL not in visited set
    - At `depth == max_depth`, save content but do not follow links
    - Build `url_to_filepath` mapping during crawl
    - Print progress messages as each page is fetched and saved
    - Return `CrawlResult` with pages scraped count and output directory
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 9.1, 9.2, 9.3, 10.3, 10.4_

  - [x] 8.2 Write property test for depth limiting (Property 5)
    - **Property 5: Depth limiting prevents link following at MAX_DEPTH**
    - Generate mock page graphs with various depths
    - Assert pages at MAX_DEPTH are saved but their child links are not enqueued
    - **Validates: Requirements 4.3**

  - [x] 8.3 Write property test for cycle prevention (Property 6)
    - **Property 6: Cycle prevention ensures each unique URL is fetched at most once**
    - Generate mock page graphs with cycles
    - Assert each unique normalized URL is fetched exactly once
    - **Validates: Requirements 5.1, 5.2**

  - [x] 8.4 Write unit tests for `crawler.py`
    - Mock fetcher, extractor, converter, writer modules
    - Test BFS order of page processing
    - Test depth limiting stops link following at MAX_DEPTH
    - Test visited set prevents duplicate fetches
    - Test error handling continues crawl on fetch/parse failures
    - Test start URL is treated as depth 0
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 9.1, 9.2, 9.3_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement link rewriter (`rewriter.py`)
  - [x] 10.1 Implement `rewrite_links(url_to_filepath, output_dir)` for post-processing
    - Read each saved Markdown file
    - Replace internal GfG URLs that exist in `url_to_filepath` with relative file paths
    - Retain original absolute URLs for pages not in the mapping
    - Write updated content back to the file
    - _Requirements: 6.1, 6.2_

  - [x] 10.2 Write property test for link rewriting (Property 7)
    - **Property 7: Link rewriting correctness**
    - Generate random URL-to-filepath mappings and Markdown content with links
    - Assert mapped URLs are replaced with correct relative paths and unmapped URLs remain unchanged
    - **Validates: Requirements 6.1, 6.2**

  - [x] 10.3 Write unit tests for `rewriter.py`
    - Test rewriting of scraped internal links to relative paths
    - Test retention of unscraped internal links as absolute URLs
    - Test handling of files with no internal links
    - _Requirements: 6.1, 6.2_

- [ ] 11. Implement CLI entry point (`cli.py`) and wire everything together
  - [x] 11.1 Implement `parse_args(argv)` using `argparse`
    - Required positional argument: starting URL
    - Optional arguments: `--max-depth` (default 2), `--output-dir` (default "output"), `--delay` (default 2.0), `--timeout` (default 30.0)
    - Return `ScraperConfig` instance
    - _Requirements: 10.1, 10.2_

  - [x] 11.2 Implement `main()` entry point
    - Parse args, call `crawl(config)`, call `rewrite_links()`, print completion summary (pages scraped, output directory)
    - Add `if __name__ == "__main__"` block
    - _Requirements: 10.3, 10.4_

  - [x] 11.3 Write unit tests for CLI parsing
    - Test required URL argument
    - Test default values for optional arguments
    - Test custom values for all optional arguments
    - Test error on missing required argument
    - _Requirements: 10.1, 10.2_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use `hypothesis` with `@settings(max_examples=100)`
- Unit tests use `pytest` with `responses` for HTTP mocking
- Checkpoints ensure incremental validation
- The link rewriter runs as a post-processing pass after all pages are crawled (two-pass design)
