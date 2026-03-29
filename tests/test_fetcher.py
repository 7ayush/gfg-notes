"""Unit tests for the fetcher module."""

import logging
from unittest.mock import patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from gfg_scraper.config import ScraperConfig
from gfg_scraper.fetcher import USER_AGENT, fetch_page


@pytest.fixture
def config():
    return ScraperConfig(start_url="https://www.geeksforgeeks.org/test", polite_delay=0)


@responses.activate
def test_successful_fetch_returns_html(config):
    html = "<html><body>Hello</body></html>"
    responses.add(responses.GET, "https://www.geeksforgeeks.org/test", body=html, status=200)

    result = fetch_page("https://www.geeksforgeeks.org/test", config)
    assert result == html


@responses.activate
def test_user_agent_is_browser_string(config):
    responses.add(responses.GET, "https://www.geeksforgeeks.org/test", body="ok", status=200)

    fetch_page("https://www.geeksforgeeks.org/test", config)

    assert responses.calls[0].request.headers["User-Agent"] == USER_AGENT


@responses.activate
def test_non_2xx_returns_none_and_logs(config, caplog):
    responses.add(responses.GET, "https://www.geeksforgeeks.org/test", status=404)

    with caplog.at_level(logging.ERROR):
        result = fetch_page("https://www.geeksforgeeks.org/test", config)

    assert result is None
    assert "Non-2xx status 404" in caplog.text


@responses.activate
def test_500_returns_none_and_logs(config, caplog):
    responses.add(responses.GET, "https://www.geeksforgeeks.org/test", status=500)

    with caplog.at_level(logging.ERROR):
        result = fetch_page("https://www.geeksforgeeks.org/test", config)

    assert result is None
    assert "Non-2xx status 500" in caplog.text


@responses.activate
def test_timeout_returns_none_and_logs(config, caplog):
    responses.add(
        responses.GET,
        "https://www.geeksforgeeks.org/test",
        body=Timeout("timed out"),
    )

    with caplog.at_level(logging.ERROR):
        result = fetch_page("https://www.geeksforgeeks.org/test", config)

    assert result is None
    assert "Timeout" in caplog.text


@responses.activate
def test_connection_error_returns_none_and_logs(config, caplog):
    responses.add(
        responses.GET,
        "https://www.geeksforgeeks.org/test",
        body=ConnectionError("connection refused"),
    )

    with caplog.at_level(logging.ERROR):
        result = fetch_page("https://www.geeksforgeeks.org/test", config)

    assert result is None
    assert "Connection error" in caplog.text


def test_polite_delay_is_applied():
    cfg = ScraperConfig(start_url="https://www.geeksforgeeks.org/test", polite_delay=1.5)

    with patch("gfg_scraper.fetcher.time.sleep") as mock_sleep, \
         patch("gfg_scraper.fetcher.requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.text = "html"
        fetch_page("https://www.geeksforgeeks.org/test", cfg)

    mock_sleep.assert_called_once_with(1.5)


@responses.activate
def test_request_timeout_is_set(config):
    responses.add(responses.GET, "https://www.geeksforgeeks.org/test", body="ok", status=200)
    config.request_timeout = 15.0

    with patch("gfg_scraper.fetcher.requests.get", wraps=None) as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.text = "ok"
        fetch_page("https://www.geeksforgeeks.org/test", config)

    mock_get.assert_called_once_with(
        "https://www.geeksforgeeks.org/test",
        headers={"User-Agent": USER_AGENT},
        timeout=15.0,
    )
