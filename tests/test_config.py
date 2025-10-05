"""Tests for configuration module."""
import json
import tempfile
from pathlib import Path

import pytest

from emas_scraper.config import SearchConfig


def test_default_config():
    """Test default configuration values."""
    cfg = SearchConfig(keywords=["$EMAS"])
    
    assert cfg.keywords == ["$EMAS"]
    assert cfg.timeout == 15
    assert cfg.max_items == 50
    assert cfg.output_file == "news_output.json"
    assert "google.com" in cfg.google_news_base


def test_config_query_property():
    """Test query property joins keywords correctly."""
    cfg = SearchConfig(keywords=["$EMAS", "Merdeka Gold"])
    assert cfg.query == "$EMAS Merdeka Gold"


def test_config_from_dict():
    """Test creating config from dictionary."""
    data = {
        "keywords": ["test", "keywords"],
        "timeout": 30,
        "max_items": 100
    }
    cfg = SearchConfig.from_dict(data)
    
    assert cfg.keywords == ["test", "keywords"]
    assert cfg.timeout == 30
    assert cfg.max_items == 100


def test_config_to_dict():
    """Test converting config to dictionary."""
    cfg = SearchConfig(keywords=["$EMAS"], timeout=20)
    data = cfg.to_dict()
    
    assert data["keywords"] == ["$EMAS"]
    assert data["timeout"] == 20
    assert "google_news_base" in data


def test_config_from_json_file():
    """Test loading config from JSON file."""
    config_data = {
        "keywords": ["$EMAS", "Test"],
        "timeout": 25,
        "max_items": 75,
        "output_file": "test_output.json"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = Path(f.name)
    
    try:
        cfg = SearchConfig.from_json_file(temp_path)
        assert cfg.keywords == ["$EMAS", "Test"]
        assert cfg.timeout == 25
        assert cfg.max_items == 75
        assert cfg.output_file == "test_output.json"
    finally:
        temp_path.unlink()