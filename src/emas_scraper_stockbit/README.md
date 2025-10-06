# Stockbit Stream Scraper

A Python web scraper for extracting stream comments from Stockbit symbol pages. This scraper handles login authentication, infinite scrolling, and data extraction from dynamic content.

## Features

- **Automatic Login**: Handles Stockbit authentication
- **Infinite Scrolling**: Automatically scrolls to load all available comments
- **Data Extraction**: Extracts usernames, comments, timestamps, likes, replies
- **Multiple Output Formats**: Supports CSV and JSON output
- **Robust Error Handling**: Comprehensive error handling and logging
- **Configurable**: Flexible configuration options

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Chrome Browser** (latest version recommended)
3. **ChromeDriver** (will be managed automatically if using webdriver-manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: JSON Configuration File (Recommended)

Edit the `stockbit_config.json` file in the module directory and input your credentials:

1. Open `src/emas_scraper_stockbit/stockbit_config.json`
2. Replace `YOUR_STOCKBIT_USERNAME_HERE` with your actual username
3. Replace `YOUR_STOCKBIT_PASSWORD_HERE` with your actual password
4. Adjust other settings as needed

The file looks like this:
```json
{
  "credentials": {
    "username": "YOUR_STOCKBIT_USERNAME_HERE",
    "password": "YOUR_STOCKBIT_PASSWORD_HERE"
  },
  "scraping": {
    "symbol": "EMAS",
    "headless": false,
    "max_scrolls": 100,
    "scroll_pause_time": 3.0
  },
  "output": {
    "format": "csv",
    "filename": null
  }
}
```

### Option 2: Environment Variables

Set your Stockbit credentials using environment variables:

```bash
# Windows
set STOCKBIT_USERNAME=your_username
set STOCKBIT_PASSWORD=your_password

# Linux/Mac
export STOCKBIT_USERNAME=your_username
export STOCKBIT_PASSWORD=your_password
```

#### Option 3: Command Line Arguments

You can pass credentials via command line arguments (less secure).

## Usage

### Command Line Interface

Basic usage:
```bash
python -m emas_scraper_stockbit
```

With custom symbol:
```bash
python -m emas_scraper_stockbit --symbol BBRI
```

With credentials via command line:
```bash
python -m emas_scraper_stockbit --username your_username --password your_password --symbol TLKM
```

Full options:
```bash
python -m emas_scraper_stockbit \
    --symbol EMAS \
    --format json \
    --output custom_filename.json \
    --headless \
    --max-scrolls 50 \
    --scroll-pause 2.0 \
    --verbose
```

### Available Options

- `--symbol`: Stock symbol to scrape (default: EMAS)
- `--username`: Stockbit username
- `--password`: Stockbit password  
- `--output`: Custom output filename
- `--format`: Output format (csv or json, default: csv)
- `--headless`: Run browser in headless mode
- `--max-scrolls`: Maximum number of scrolls (default: 100)
- `--scroll-pause`: Pause time between scrolls in seconds (default: 3.0)
- `--verbose`: Enable verbose logging

### Programmatic Usage

```python
from emas_scraper_stockbit.config import StockbitConfig
from emas_scraper_stockbit.scraper import StockbitScraper

# Create configuration
config = StockbitConfig(
    username="your_username",
    password="your_password", 
    symbol="EMAS",
    output_format="csv",
    headless=False
)

# Create and run scraper
scraper = StockbitScraper(config)
success = scraper.scrape()

if success:
    # Save data
    output_file = scraper.save_data()
    print(f"Data saved to: {output_file}")
    
    # Get summary
    summary = scraper.get_summary()
    print(f"Total comments: {summary['total_comments']}")
```

## Output Format

### CSV Format
The scraper outputs data in the following CSV format:

| username | full_name | timestamp | comment_text | likes | replies | post_id |
|----------|-----------|-----------|--------------|-------|---------|-----------|---------|
| investorA | John Doe | 2025-10-06T10:30:15 | "Analisa saya, EMAS akan..." | 15 | 3 | bullish | post123 |

### JSON Format
```json
[
  {
    "username": "investorA",
    "full_name": "John Doe", 
    "timestamp": "2025-10-06T10:30:15",
    "comment_text": "Analisa saya, EMAS akan...",
    "likes": 15,
    "replies": 3,

    "post_id": "post123"
  }
]
```

## Configuration Options

The scraper can be configured through the `StockbitConfig` class:

```python
config = StockbitConfig(
    # Credentials
    username="your_username",
    password="your_password",
    
    # Target
    symbol="EMAS",
    
    # Browser settings
    headless=False,
    implicit_wait=10,
    page_load_timeout=30,
    
    # Scrolling settings
    scroll_pause_time=3.0,
    max_scrolls=100,
    
    # Output settings
    output_format="csv",
    output_filename="stockbit_stream_EMAS.csv"
)
```

## Error Handling

The scraper includes comprehensive error handling:

- **Login failures**: Detailed error messages for authentication issues
- **Network timeouts**: Configurable timeouts with retry logic
- **Element detection**: Multiple fallback selectors for robust element finding
- **Data validation**: Validates extracted data before saving

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   - Install webdriver-manager: `pip install webdriver-manager`
   - Or download ChromeDriver manually and add to PATH

2. **Login fails**
   - Verify credentials are correct
   - Check if Stockbit has changed their login form
   - Try running without headless mode to see what's happening

3. **No data extracted**
   - Stockbit may have changed their HTML structure
   - Check the page manually to see current selectors
   - Enable verbose logging to see what's being detected

4. **Infinite scroll not working**  
   - Reduce scroll pause time
   - Increase max scrolls limit
   - Check if page requires different scroll trigger

### Debug Mode

Run with verbose logging to see detailed information:

```bash
python -m emas_scraper_stockbit --verbose
```

## Security Notes

- **Never hardcode credentials** in your scripts
- Use environment variables or secure credential storage
- Be respectful of website terms of service
- Add appropriate delays to avoid overloading servers

## License

This project is for educational and research purposes. Please respect Stockbit's terms of service and robots.txt when using this scraper.