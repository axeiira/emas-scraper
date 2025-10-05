import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SearchConfig:
    keywords: List[str]
    google_news_base: str = "https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )
    timeout: int = 15
    max_items: int = 50
    output_file: str = "news_output.json"

    @property
    def query(self) -> str:
        # Join keywords with spaces; allow user to pass quoted tokens like "$EMAS"
        return " ".join(self.keywords).strip()

    @classmethod
    def from_json_file(cls, config_path: Path) -> "SearchConfig":
        """Load configuration from JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "SearchConfig":
        """Create configuration from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'keywords': self.keywords,
            'google_news_base': self.google_news_base,
            'user_agent': self.user_agent,
            'timeout': self.timeout,
            'max_items': self.max_items,
            'output_file': self.output_file
        }
