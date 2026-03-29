"""CLI entry point for the GfG Web Scraper."""

import argparse

from gfg_scraper.config import ScraperConfig
from gfg_scraper.crawler import crawl
from gfg_scraper.rewriter import rewrite_links


def parse_args(argv: list[str] | None = None) -> ScraperConfig:
    """Parse CLI arguments and return a ScraperConfig."""
    parser = argparse.ArgumentParser(
        description="Recursively scrape GeeksforGeeks articles to Markdown."
    )
    parser.add_argument("url", help="Starting URL to scrape")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum recursion depth (default: 2)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Maximum number of pages to scrape, 0 for no limit (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help='Output directory (default: "output")',
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Polite delay between requests per worker in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of parallel workers (default: 3)",
    )

    args = parser.parse_args(argv)

    return ScraperConfig(
        start_url=args.url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        workers=args.workers,
        output_dir=args.output_dir,
        polite_delay=args.delay,
        request_timeout=args.timeout,
    )


def main() -> None:
    """Run the GfG Web Scraper: parse args, crawl, rewrite links, print summary."""
    config = parse_args()
    result, url_to_filepath = crawl(config)
    rewrite_links(url_to_filepath, config.output_dir)
    print(f"Scraping complete! {result.pages_scraped} pages saved to {result.output_dir}")


if __name__ == "__main__":
    main()
