from __future__ import annotations

import html
import json
import logging
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional
from urllib.parse import quote_plus, unquote

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from .config import SearchConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    url: str
    source: Optional[str]
    publication_date: Optional[str]  # ISO date


def build_search_url(cfg: SearchConfig) -> str:
    """Build Google News RSS search URL from configuration."""
    q = quote_plus(cfg.query)
    url = cfg.google_news_base.format(query=q)
    logger.info(f"Built search URL: {url}")
    return url


def fetch(url: str, user_agent: str, timeout: int) -> str:
    """Fetch content from URL with proper headers and error handling."""
    headers = {"User-Agent": user_agent}
    
    try:
        logger.info(f"Fetching URL: {url}")
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        logger.info(f"Successfully fetched {len(resp.text)} characters")
        return resp.text
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout} seconds")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def parse_google_news_rss(xml_text: str, max_items: int = 50) -> List[NewsItem]:
    """Parse Google News RSS feed and extract news items."""
    try:
        soup = BeautifulSoup(xml_text, "xml")
        items = []
        
        rss_items = soup.find_all("item")
        logger.info(f"Found {len(rss_items)} RSS items, processing up to {max_items}")
        
        for item in rss_items[:max_items]:
            try:
                # Extract title
                title = item.title.text.strip() if item.title else ""
                title = html.unescape(title)
                
                # Extract URL
                link_tag = item.link
                url = link_tag.text.strip() if link_tag else ""
                
                # Extract source (from source tag or try to extract from URL)
                source = None
                source_tag = item.find("source")
                if source_tag and source_tag.text:
                    source = source_tag.text.strip()
                elif url:
                    # Try to extract domain as source
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        if domain:
                            source = domain.replace('www.', '')
                    except Exception:
                        pass
                
                # Extract publication date
                pub_date = None
                if item.pubDate and item.pubDate.text:
                    try:
                        dt = dateparser.parse(item.pubDate.text, fuzzy=True)
                        if dt:
                            pub_date = dt.date().isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date '{item.pubDate.text}': {e}")
                
                # Only add items with title and URL
                if title and url:
                    news_item = NewsItem(
                        title=title, 
                        url=url, 
                        source=source, 
                        publication_date=pub_date
                    )
                    items.append(news_item)
                    
            except Exception as e:
                logger.warning(f"Failed to parse RSS item: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(items)} news items")
        return items
        
    except Exception as e:
        logger.error(f"Failed to parse RSS feed: {e}")
        return []


def search_google_news(cfg: SearchConfig) -> List[NewsItem]:
    """Main function to search Google News and return parsed news items."""
    logger.info(f"Starting Google News search with query: '{cfg.query}'")
    
    url = build_search_url(cfg)
    xml_text = fetch(url, user_agent=cfg.user_agent, timeout=cfg.timeout)
    items = parse_google_news_rss(xml_text, max_items=cfg.max_items)
    
    logger.info(f"Search completed. Found {len(items)} items")
    return items


def serialize_results(items: Iterable[NewsItem]) -> str:
    return json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2)
