"""Unit tests for CLI argument parsing and main entry point."""

from unittest.mock import patch, MagicMock

import pytest

from gfg_scraper.cli import parse_args, main
from gfg_scraper.config import CrawlResult, ScraperConfig


class TestParseArgs:
    """Tests for parse_args function."""

    def test_required_url_argument(self):
        config = parse_args(["https://www.geeksforgeeks.org/data-structures/"])
        assert config.start_url == "https://www.geeksforgeeks.org/data-structures/"

    def test_default_values(self):
        config = parse_args(["https://www.geeksforgeeks.org/"])
        assert config.max_depth == 2
        assert config.output_dir == "output"
        assert config.polite_delay == 2.0
        assert config.request_timeout == 30.0

    def test_custom_max_depth(self):
        config = parse_args(["https://www.geeksforgeeks.org/", "--max-depth", "5"])
        assert config.max_depth == 5

    def test_custom_output_dir(self):
        config = parse_args(["https://www.geeksforgeeks.org/", "--output-dir", "docs"])
        assert config.output_dir == "docs"

    def test_custom_delay(self):
        config = parse_args(["https://www.geeksforgeeks.org/", "--delay", "0.5"])
        assert config.polite_delay == 0.5

    def test_custom_timeout(self):
        config = parse_args(["https://www.geeksforgeeks.org/", "--timeout", "60.0"])
        assert config.request_timeout == 60.0

    def test_all_custom_values(self):
        config = parse_args([
            "https://www.geeksforgeeks.org/arrays/",
            "--max-depth", "3",
            "--output-dir", "my_output",
            "--delay", "1.5",
            "--timeout", "45.0",
        ])
        assert config.start_url == "https://www.geeksforgeeks.org/arrays/"
        assert config.max_depth == 3
        assert config.output_dir == "my_output"
        assert config.polite_delay == 1.5
        assert config.request_timeout == 45.0

    def test_returns_scraper_config_instance(self):
        config = parse_args(["https://www.geeksforgeeks.org/"])
        assert isinstance(config, ScraperConfig)

    def test_missing_url_raises_error(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestMain:
    """Tests for main() entry point."""

    @patch("gfg_scraper.cli.rewrite_links")
    @patch("gfg_scraper.cli.crawl")
    @patch("gfg_scraper.cli.parse_args")
    def test_main_calls_crawl_and_rewrite(self, mock_parse, mock_crawl, mock_rewrite):
        config = ScraperConfig(start_url="https://www.geeksforgeeks.org/test/")
        url_map = {"https://www.geeksforgeeks.org/test/": "output/01_test.md"}
        mock_parse.return_value = config
        mock_crawl.return_value = (CrawlResult(pages_scraped=1, output_dir="output"), url_map)

        main()

        mock_parse.assert_called_once()
        mock_crawl.assert_called_once_with(config)
        mock_rewrite.assert_called_once_with(url_map, "output")

    @patch("gfg_scraper.cli.rewrite_links")
    @patch("gfg_scraper.cli.crawl")
    @patch("gfg_scraper.cli.parse_args")
    def test_main_prints_summary(self, mock_parse, mock_crawl, mock_rewrite, capsys):
        config = ScraperConfig(start_url="https://www.geeksforgeeks.org/")
        mock_parse.return_value = config
        mock_crawl.return_value = (CrawlResult(pages_scraped=5, output_dir="my_output"), {})

        main()

        captured = capsys.readouterr()
        assert "5 pages saved to my_output" in captured.out
