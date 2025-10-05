from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .config import SearchConfig
from .google_news import search_google_news, serialize_results
from .sentiment_analyzer import analyze_news_sentiment


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EMAS Scraper - News scraping and sentiment analysis for $EMAS",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command (default)
    scrape_parser = subparsers.add_parser('scrape', help='Scrape news articles')
    scrape_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to JSON configuration file (default: config.json if exists)",
    )
    scrape_parser.add_argument(
        "--keywords",
        nargs="+",
        help="Daftar kata kunci untuk pencarian (override config file)",
    )
    scrape_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="File output JSON (override config file)",
    )
    scrape_parser.add_argument(
        "--max-items", 
        type=int, 
        help="Maksimum item yang diambil (override config file)"
    )
    scrape_parser.add_argument(
        "--timeout",
        type=int,
        help="Request timeout in seconds (override config file)"
    )
    
    # Sentiment analysis command
    sentiment_parser = subparsers.add_parser('analyze-sentiment', help='Analyze sentiment of scraped news')
    sentiment_parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("news_output.json"),
        help="Input JSON file with news articles (default: news_output.json)"
    )
    sentiment_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("sentiment_analysis.json"),
        help="Output JSON file for sentiment analysis (default: sentiment_analysis.json)"
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # If no command specified, default to scrape
    if args.command is None:
        args.command = 'scrape'
        # Copy all scrape arguments to main args for backward compatibility
        if not hasattr(args, 'config'):
            args.config = None
            args.keywords = None
            args.output = None
            args.max_items = None
            args.timeout = None
    
    return args


def load_config(args: argparse.Namespace) -> SearchConfig:
    """Load configuration from file or create default."""
    config_path = args.config
    
    # Try to find default config file if not specified
    if not config_path:
        default_config = Path("config.json")
        if default_config.exists():
            config_path = default_config
    
    # Load from file if available
    if config_path and config_path.exists():
        cfg = SearchConfig.from_json_file(config_path)
        print(f"Loaded configuration from {config_path}")
    else:
        # Create default configuration
        cfg = SearchConfig(
            keywords=["$EMAS", "Merdeka Gold", "Merdeka Copper Gold"],
            max_items=50
        )
        if config_path:
            print(f"Warning: Config file {config_path} not found, using defaults")
    
    # Override with command line arguments
    if args.keywords:
        cfg.keywords = args.keywords
    if args.output:
        cfg.output_file = str(args.output)
    if args.max_items:
        cfg.max_items = args.max_items
    if args.timeout:
        cfg.timeout = args.timeout
    
    return cfg


def main_scrape(args: argparse.Namespace) -> int:
    """Main function for scraping news."""
    cfg = load_config(args)
    
    print(f"Mencari berita dengan kata kunci: {cfg.keywords}")
    print(f"Maksimum item: {cfg.max_items}")
    
    items = search_google_news(cfg)
    json_text = serialize_results(items)
    
    output_path = Path(cfg.output_file)
    output_path.write_text(json_text, encoding="utf-8")
    
    print(f"Berhasil menyimpan {len(items)} item ke {output_path}")
    
    # Print summary
    if items:
        print("\nRingkasan hasil:")
        for i, item in enumerate(items[:5], 1):
            print(f"{i}. {item.title[:80]}...")
        if len(items) > 5:
            print(f"... dan {len(items) - 5} item lainnya")
    
    return 0


def main_sentiment(args: argparse.Namespace) -> int:
    """Main function for sentiment analysis."""
    input_file = args.input
    output_file = args.output
    
    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Input file tidak ditemukan: {input_file}")
        print(f"Jalankan 'emas-scraper scrape' terlebih dahulu untuk mengumpulkan berita.")
        return 1
    
    print(f"🔍 Menganalisis sentiment dari: {input_file}")
    print(f"📊 Output akan disimpan ke: {output_file}")
    print(f"⏳ Memuat model Indonesian BERT... (mungkin perlu download ~400MB)")
    
    # Perform sentiment analysis
    success = analyze_news_sentiment(input_file, output_file)
    
    if success:
        print(f"✅ Analisis sentiment selesai! Lihat hasil di: {output_file}")
        return 0
    else:
        print(f"❌ Analisis sentiment gagal!")
        return 1


def main(argv: List[str] | None = None) -> int:
    """Main entry point with command routing."""
    args = parse_args(argv)
    
    if args.command == 'scrape':
        return main_scrape(args)
    elif args.command == 'analyze-sentiment':
        return main_sentiment(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
