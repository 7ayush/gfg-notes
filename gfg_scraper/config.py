"""Configuration and data models for the GfG Web Scraper."""

from dataclasses import dataclass, field


@dataclass
class ScraperConfig:
    """Configuration for the scraper."""

    start_url: str
    max_depth: int = 2
    max_pages: int = 0  # 0 means no limit
    workers: int = 3
    output_dir: str = "output"
    polite_delay: float = 1.0
    request_timeout: float = 30.0


@dataclass
class PageRecord:
    """Tracks metadata for each scraped page during the crawl."""

    url: str
    depth: int
    discovery_order: int
    file_path: str
    parent_dir: str
    child_links: list[str] = field(default_factory=list)


@dataclass
class CrawlResult:
    """Summary of a completed crawl."""

    pages_scraped: int
    output_dir: str
