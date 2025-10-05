"""Tests for Google News scraper module."""
from unittest.mock import Mock, patch

import pytest

from emas_scraper.config import SearchConfig
from emas_scraper.google_news import (
    NewsItem,
    build_search_url,
    fetch,
    parse_google_news_rss,
    search_google_news
)


def test_news_item():
    """Test NewsItem dataclass."""
    item = NewsItem(
        title="Test Title",
        url="https://example.com",
        source="Example.com",
        publication_date="2025-10-05"
    )
    
    assert item.title == "Test Title"
    assert item.url == "https://example.com"
    assert item.source == "Example.com"
    assert item.publication_date == "2025-10-05"


def test_build_search_url():
    """Test URL building with proper encoding."""
    cfg = SearchConfig(keywords=["$EMAS", "test"])
    url = build_search_url(cfg)
    
    assert "news.google.com" in url
    assert "search" in url
    assert "%24EMAS" in url  # URL encoded $
    assert "test" in url


def test_parse_google_news_rss():
    """Test RSS parsing with mock data."""
    mock_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Google News</title>
            <item>
                <title>Test News Title</title>
                <link>https://example.com/news1</link>
                <pubDate>Sat, 05 Oct 2025 10:00:00 GMT</pubDate>
                <source url="https://example.com">Example.com</source>
            </item>
            <item>
                <title>Another News &amp; Title</title>
                <link>https://test.com/news2</link>
                <pubDate>Fri, 04 Oct 2025 15:30:00 GMT</pubDate>
            </item>
        </channel>
    </rss>"""
    
    items = parse_google_news_rss(mock_rss, max_items=10)
    
    assert len(items) == 2
    
    # First item
    assert items[0].title == "Test News Title"
    assert items[0].url == "https://example.com/news1"
    assert items[0].source == "Example.com"
    assert items[0].publication_date == "2025-10-05"
    
    # Second item (HTML unescaping test)
    assert items[1].title == "Another News & Title"
    assert items[1].url == "https://test.com/news2"
    assert items[1].publication_date == "2025-10-04"


def test_parse_google_news_rss_max_items():
    """Test RSS parsing respects max_items limit."""
    mock_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Google News</title>
            <item><title>News 1</title><link>https://example.com/1</link></item>
            <item><title>News 2</title><link>https://example.com/2</link></item>
            <item><title>News 3</title><link>https://example.com/3</link></item>
        </channel>
    </rss>"""
    
    items = parse_google_news_rss(mock_rss, max_items=2)
    assert len(items) == 2
    assert items[0].title == "News 1"
    assert items[1].title == "News 2"


def test_parse_google_news_rss_empty():
    """Test RSS parsing with empty/invalid content."""
    items = parse_google_news_rss("", max_items=10)
    assert len(items) == 0
    
    items = parse_google_news_rss("invalid xml", max_items=10)
    assert len(items) == 0


@patch('emas_scraper.google_news.requests.get')
def test_fetch_success(mock_get):
    """Test successful HTTP fetch."""
    mock_response = Mock()
    mock_response.text = "test content"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    content = fetch("https://example.com", "test-agent", 30)
    
    assert content == "test content"
    mock_get.assert_called_once_with(
        "https://example.com",
        headers={"User-Agent": "test-agent"},
        timeout=30
    )


@patch('emas_scraper.google_news.requests.get')
def test_fetch_timeout(mock_get):
    """Test HTTP fetch timeout handling."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout()
    
    with pytest.raises(requests.exceptions.Timeout):
        fetch("https://example.com", "test-agent", 30)


@patch('emas_scraper.google_news.fetch')
@patch('emas_scraper.google_news.parse_google_news_rss')
def test_search_google_news_integration(mock_parse, mock_fetch):
    """Test the main search function integration."""
    mock_fetch.return_value = "mock rss content"
    mock_parse.return_value = [
        NewsItem("Test", "https://example.com", "Example", "2025-10-05")
    ]
    
    cfg = SearchConfig(keywords=["$EMAS"])
    items = search_google_news(cfg)
    
    assert len(items) == 1
    assert items[0].title == "Test"
    
    mock_fetch.assert_called_once()
    mock_parse.assert_called_once_with("mock rss content", max_items=50)