"""
Command Line Interface for Stockbit Stream Scraper
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from .config import StockbitConfig
    from .scraper import StockbitScraper
except ImportError:
    from config import StockbitConfig
    from scraper import StockbitScraper


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Stockbit Stream Scraper - Extract comments from Stockbit symbol pages"
    )
    
    parser.add_argument(
        "--symbol", 
        default="EMAS",
        help="Stock symbol to scrape (default: EMAS)"
    )
    
    parser.add_argument(
        "--username",
        help="Stockbit username (can also be set via STOCKBIT_USERNAME environment variable)"
    )
    
    parser.add_argument(
        "--password",
        help="Stockbit password (can also be set via STOCKBIT_PASSWORD environment variable)"
    )
    
    parser.add_argument(
        "--output",
        help="Output filename (default: stockbit_stream_{SYMBOL}.csv)"
    )
    
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=100,
        help="Maximum number of scrolls to perform (default: 100)"
    )
    
    parser.add_argument(
        "--scroll-pause",
        type=float,
        default=3.0,
        help="Time to pause between scrolls in seconds (default: 3.0)"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to JSON configuration file"
    )
    
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Manual login mode - assumes user is already logged in to Stockbit"
    )
    
    parser.add_argument(
        "--session",
        action="store_true",
        help="Session reuse mode - connects to existing Chrome browser with debugging enabled"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Load configuration from INI file
    try:
        config_path = args.config if args.config else None
        config = StockbitConfig.from_ini_file(config_path)
        if args.config:
            print(f"📄 Loaded configuration from: {args.config}")
        else:
            print("📄 Loaded configuration from config.ini")
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        print("Using default configuration...")
        config = StockbitConfig()
    
    # Override config with command line arguments if provided
    if args.symbol:
        config.symbol = args.symbol
    if args.username:
        config.username = args.username
    if args.password:
        config.password = args.password
    if args.output:
        config.output_filename = args.output
    if args.format:
        config.output_format = args.format
    if args.headless:
        config.headless = args.headless
    if args.max_scrolls:
        config.max_scrolls = args.max_scrolls
    if args.scroll_pause:
        config.scroll_pause_time = args.scroll_pause
    
    # Check if session reuse mode is requested
    if args.session:
        print("🔧 SESSION REUSE MODE SELECTED")
        print("=" * 50)
        print("This mode connects to your existing Chrome browser.")
        print("Please follow these steps first:")
        print()
        print("1. Close all Chrome windows")
        print("2. Run: start_chrome_debug.bat")
        print("3. In the Chrome that opens, login to Stockbit and go to EMAS page")
        print("4. Come back here and continue")
        print()
        
        input("Press Enter when you're ready to connect to your browser...")
        print("\n🚀 Connecting to existing browser session...")
        
        session_mode = True
        manual_mode = False
    elif args.manual:
        print("🔧 MANUAL LOGIN MODE SELECTED")
        print("=" * 50)
        print("Please follow these steps:")
        print("1. Open a browser and go to https://stockbit.com/login")
        print("2. Log in with your credentials manually")
        print(f"3. Navigate to https://stockbit.com/symbol/{config.symbol}")
        print("4. Make sure you can see the Stream section")
        print("5. Keep this browser window open")
        print()
        
        input("Press Enter when you're logged in and on the symbol page...")
        print("\n🚀 Starting scraper in manual mode...")
        
        session_mode = False
        manual_mode = True
    else:
        session_mode = False
        manual_mode = False
        # Validate credentials for automatic mode
        if not session_mode and not config.validate_credentials():
            print("ERROR: Please provide valid credentials via one of these methods:")
            print("  1. Edit config.ini file and input your credentials")
            print("  2. Command line arguments: --username and --password")
            print("  3. Environment variables: STOCKBIT_USERNAME and STOCKBIT_PASSWORD")
            print("  4. Use --manual flag to login manually")
            print("  5. Use --session flag to reuse existing browser session")
            print("\nExample usage:")
            print("  python -m emas_scraper_stockbit --username your_username --password your_password")
            print("  python -m emas_scraper_stockbit --symbol BBRI --format json")
            print("  python -m emas_scraper_stockbit --manual")
            print("  python -m emas_scraper_stockbit --session")
            print(f"\nConfig file location: config.ini")
            sys.exit(1)
    
    print(f"Starting Stockbit scraper for symbol: {config.symbol}")
    print(f"Output will be saved to: {config.output_filename}")
    
    # Create scraper and run
    scraper = StockbitScraper(config)
    
    try:
        if session_mode:
            success = scraper.scrape_session_mode()
        elif manual_mode:
            success = scraper.scrape_manual_mode()
        else:
            success = scraper.scrape()
        
        if success:
            # Save data
            output_file = scraper.save_data()
            print(f"\n✅ Scraping completed successfully!")
            print(f"📁 Data saved to: {output_file}")
            
            # Print summary
            summary = scraper.get_summary()
            print(f"\n📊 Summary:")
            print(f"  Total comments: {summary.get('total_comments', 0)}")
            print(f"  Unique users: {summary.get('unique_users', 0)}")
            print(f"  Total likes: {summary.get('total_likes', 0)}")
            print(f"  Total replies: {summary.get('total_replies', 0)}")
            
            if summary.get('date_range', {}).get('earliest'):
                print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        else:
            print("\n❌ Scraping failed. Check the logs for more details.")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()