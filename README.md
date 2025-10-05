# EMAS Scraper

A dynamic web scraper for PT Merdeka Gold Resources Tbk ($EMAS) news articles using Google News RSS feeds.

## Features

- **Dynamic news discovery** via Google News RSS (no manual source management)
- **Indonesian sentiment analysis** using BERT with TextBlob fallback (100% free)
- **Configurable keywords** via JSON config file or command line
- **Structured JSON output** with title, URL, source, and publication date
- **Comprehensive sentiment reports** with positive/negative/neutral classification
- **Robust error handling** and logging
- **Comprehensive test suite** with pytest
- **CLI interface** with flexible configuration options

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd emas-scraper
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install in development mode:
```bash
pip install -e .
```

## Usage

### Command Line Interface

**Scrape news articles:**
```bash
# Default scraping
emas-scraper scrape

# With custom parameters
emas-scraper scrape --keywords "$EMAS" "Merdeka Gold" --max-items 10 --output my_news.json

# Using custom config file
emas-scraper scrape --config my_config.json
```

**Analyze sentiment:**
```bash
# Analyze sentiment of scraped news
emas-scraper analyze-sentiment

# With custom input/output files
emas-scraper analyze-sentiment --input my_news.json --output my_sentiment.json
```

**Complete workflow:**
```bash
# 1. Scrape news
emas-scraper scrape --max-items 20

# 2. Analyze sentiment
emas-scraper analyze-sentiment
```

### Configuration

Create a `config.json` file in the project root:

```json
{
  "keywords": [
    "$EMAS",
    "Merdeka Gold", 
    "Merdeka Copper Gold",
    "PT Merdeka Gold Resources"
  ],
  "google_news_base": "https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "timeout": 15,
  "max_items": 50,
  "output_file": "news_output.json"
}
```

### Python API

```python
from emas_scraper.config import SearchConfig
from emas_scraper.google_news import search_google_news
from emas_scraper.sentiment_analyzer import analyze_news_sentiment
from pathlib import Path

# Create configuration
config = SearchConfig(keywords=["$EMAS", "Merdeka Gold"])

# Search for news
news_items = search_google_news(config)

# Process results
for item in news_items:
    print(f"{item.title} - {item.source}")

# Analyze sentiment
input_file = Path("news_output.json")
output_file = Path("sentiment_analysis.json")
analyze_news_sentiment(input_file, output_file)
```

## Architecture

The scraper follows a modular architecture:

1. **Configuration Module** (`config.py`):
   - Loads settings from JSON files or defaults
   - Supports command-line overrides

2. **Google News Module** (`google_news.py`):
   - Builds search URLs with proper encoding
   - Fetches RSS feeds with proper headers
   - Parses RSS XML and extracts metadata

3. **CLI Module** (`cli.py`):
   - Provides command-line interface with subcommands
   - Handles argument parsing and config loading
   - Outputs results with summary

4. **Sentiment Analysis Module** (`sentiment_analyzer.py`):
   - Uses Indonesian BERT model for accurate sentiment analysis
   - Falls back to TextBlob for reliability
   - Generates comprehensive analysis reports
   - Supports batch processing

## Output Format

### News Scraping Output

The scraper outputs JSON with the following structure:

```json
[
  {
    "title": "News article title",
    "url": "https://example.com/article",
    "source": "Source Name", 
    "publication_date": "2025-10-05"
  }
]
```

### Sentiment Analysis Output

The sentiment analyzer outputs comprehensive reports:

```json
{
  "analysis_metadata": {
    "analysis_date": "2025-10-05T15:30:00",
    "source_file": "news_output.json",
    "total_articles": 10,
    "analysis_methods_used": {"indonesian_bert": 8, "textblob_fallback": 2}
  },
  "sentiment_summary": {
    "by_sentiment": {"positive": 6, "negative": 2, "neutral": 2},
    "by_confidence": {"high": 4, "medium": 3, "low": 3},
    "sentiment_percentages": {"positive": 60.0, "negative": 20.0, "neutral": 20.0}
  },
  "detailed_results": [
    {
      "title": "Article title",
      "url": "https://example.com/article",
      "source": "Source Name",
      "publication_date": "2025-10-05",
      "sentiment": {
        "label": "positive",
        "score": 0.85,
        "confidence": "high"
      },
      "analysis_method": "indonesian_bert"
    }
  ]
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=emas_scraper

# Run specific test file
pytest tests/test_google_news.py -v
```

### Project Structure

```
emas-scraper/
├── src/emas_scraper/
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface with subcommands
│   ├── config.py              # Configuration management
│   ├── google_news.py         # Google News RSS scraper  
│   └── sentiment_analyzer.py  # Indonesian BERT sentiment analysis
├── tests/
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_google_news.py
│   └── test_sentiment_analyzer.py
├── config.json                # Default configuration
├── pyproject.toml             # Project metadata
└── requirements.txt           # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License

---

**Note:** Use responsibly and ethically. Respect robots.txt and Terms of Service of relevant sites. The scraper makes only one request to Google News RSS.
