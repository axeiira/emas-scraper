"""
Example usage script for Stockbit Stream Scraper
"""

import os
from pathlib import Path

from config import StockbitConfig
from scraper import StockbitScraper


def main():
    """Example of how to use the Stockbit scraper programmatically"""
    
    # Load configuration from config.ini file
    config = StockbitConfig.from_ini_file()
    
    if not config.validate_credentials():
        print("⚠️  Please configure your credentials in config.ini file:")
        print("   Edit the [credentials] section with your Stockbit username and password")
        return
    
    # You can override specific settings if needed
    config.max_scrolls = 50  # Limit scrolling for testing
    config.scroll_pause_time = 2.0  # Faster scrolling for testing
    
    print(f"🚀 Starting Stockbit scraper for symbol: {config.symbol}")
    print(f"📊 Output will be saved as: {config.output_filename}")
    
    # Create and run the scraper
    scraper = StockbitScraper(config)
    
    try:
        # Perform the scraping
        success = scraper.scrape()
        
        if success:
            # Save the data
            output_file = scraper.save_data()
            print(f"\n✅ Scraping completed successfully!")
            print(f"📁 Data saved to: {output_file}")
            
            # Display summary statistics
            summary = scraper.get_summary()
            print(f"\n📈 Summary Statistics:")
            print(f"   Total comments: {summary.get('total_comments', 0)}")
            print(f"   Unique users: {summary.get('unique_users', 0)}")
            print(f"   Total likes: {summary.get('total_likes', 0)}")
            print(f"   Total replies: {summary.get('total_replies', 0)}")
            
            # Date range
            date_range = summary.get('date_range', {})
            if date_range.get('earliest'):
                print(f"   Date range: {date_range['earliest']} to {date_range['latest']}")
            

            
            # Show first few comments as preview
            if scraper.data_manager.comments:
                print(f"\n📝 Sample comments (first 3):")
                for i, comment in enumerate(scraper.data_manager.comments[:3]):
                    print(f"   {i+1}. @{comment.username}: {comment.comment_text[:100]}...")
                    print(f"      Likes: {comment.likes}, Replies: {comment.replies}")
                    print()
        
        else:
            print("\n❌ Scraping failed. Check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()