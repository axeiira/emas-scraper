"""Tests for CLI module."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from emas_scraper.cli import load_config, main, parse_args
from emas_scraper.config import SearchConfig
from emas_scraper.google_news import NewsItem


def test_parse_args_defaults():
    """Test argument parsing with defaults."""
    args = parse_args([])
    
    assert args.command == 'scrape'
    assert args.config is None
    assert args.keywords is None
    assert args.output is None
    assert args.max_items is None


def test_parse_args_with_values():
    """Test argument parsing with provided values."""
    args = parse_args([
        "scrape",
        "--config", "test_config.json",
        "--keywords", "$EMAS", "test",
        "--output", "test_output.json",
        "--max-items", "25",
        "--timeout", "45"
    ])
    
    assert args.command == "scrape"
    assert args.config == Path("test_config.json")
    assert args.keywords == ["$EMAS", "test"]
    assert args.output == Path("test_output.json")
    assert args.max_items == 25
    assert args.timeout == 45


def test_parse_args_sentiment_command():
    """Test argument parsing for sentiment analysis command."""
    args = parse_args([
        "analyze-sentiment",
        "--input", "my_news.json",
        "--output", "my_sentiment.json"
    ])
    
    assert args.command == "analyze-sentiment"
    assert args.input == Path("my_news.json")
    assert args.output == Path("my_sentiment.json")


def test_load_config_default():
    """Test loading default configuration."""
    with patch('pathlib.Path.exists', return_value=False):
        args = Mock()
        args.config = None
        args.keywords = None
        args.output = None
        args.max_items = None
        args.timeout = None
        
        cfg = load_config(args)
        
        assert "$EMAS" in cfg.keywords
        assert cfg.max_items == 50


def test_load_config_from_file():
    """Test loading configuration from file."""
    config_data = {
        "keywords": ["test", "config"],
        "timeout": 25,
        "max_items": 75
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = Path(f.name)
    
    try:
        args = Mock()
        args.config = temp_path
        args.keywords = None
        args.output = None
        args.max_items = None
        args.timeout = None
        
        cfg = load_config(args)
        
        assert cfg.keywords == ["test", "config"]
        assert cfg.timeout == 25
        assert cfg.max_items == 75
    finally:
        temp_path.unlink()


def test_load_config_with_overrides():
    """Test configuration loading with command line overrides."""
    config_data = {
        "keywords": ["original"],
        "max_items": 50
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = Path(f.name)
    
    try:
        args = Mock()
        args.config = temp_path
        args.keywords = ["overridden", "keywords"]
        args.output = Path("override_output.json")
        args.max_items = 25
        args.timeout = 20
        
        cfg = load_config(args)
        
        assert cfg.keywords == ["overridden", "keywords"]
        assert cfg.output_file == "override_output.json"
        assert cfg.max_items == 25
        assert cfg.timeout == 20
    finally:
        temp_path.unlink()


@patch('emas_scraper.cli.search_google_news')
@patch('emas_scraper.cli.load_config')
def test_main_success(mock_load_config, mock_search):
    """Test successful main execution."""
    # Setup mocks
    mock_cfg = Mock()
    mock_cfg.keywords = ["$EMAS"]
    mock_cfg.max_items = 50
    mock_cfg.output_file = "test_output.json"
    mock_load_config.return_value = mock_cfg
    
    mock_items = [
        NewsItem("Test Title", "https://example.com", "Example", "2025-10-05")
    ]
    mock_search.return_value = mock_items
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.json"
        mock_cfg.output_file = str(output_path)
        
        # Run main
        result = main([])
        
        assert result == 0
        assert output_path.exists()
        
        # Check output content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["title"] == "Test Title"
        assert data[0]["url"] == "https://example.com"


@patch('emas_scraper.cli.search_google_news')
@patch('emas_scraper.cli.load_config')
def test_main_no_results(mock_load_config, mock_search):
    """Test main execution with no results."""
    mock_cfg = Mock()
    mock_cfg.keywords = ["$EMAS"]
    mock_cfg.max_items = 50
    mock_cfg.output_file = "empty_output.json"
    mock_load_config.return_value = mock_cfg
    
    mock_search.return_value = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "empty_output.json"
        mock_cfg.output_file = str(output_path)
        
        result = main([])
        
        assert result == 0
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data == []