"""
Manual Login Mode Scraper - assumes user is already logged in
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import StockbitConfig
from scraper import StockbitScraper
import time

def manual_login_scraper():
    """
    Scraper that assumes user is already logged in manually
    """
    
    # Load config
    config = StockbitConfig.from_ini_file()
    
    print("🔧 MANUAL LOGIN MODE")
    print("=" * 50)
    print("Please follow these steps:")
    print("1. Open a browser and go to https://stockbit.com/login")
    print("2. Log in with your credentials manually")
    print("3. Navigate to https://stockbit.com/symbol/EMAS")
    print("4. Make sure you can see the Stream section")
    print("5. Keep this browser window open")
    print()
    
    input("Press Enter when you're logged in and on the EMAS page...")
    
    print("\n🚀 Starting scraper in manual mode...")
    
    # Create scraper but skip login
    scraper = StockbitScraper(config)
    
    try:
        # Initialize driver
        scraper.driver = scraper._init_driver()
        print("✅ WebDriver initialized")
        
        # Navigate directly to EMAS page (user should already be logged in)
        print(f"📍 Navigating to EMAS page: {config.symbol_url}")
        scraper.driver.get(config.symbol_url)
        
        # Wait for page to load
        time.sleep(5)
        
        current_url = scraper.driver.current_url
        print(f"📍 Current URL: {current_url}")
        print(f"📄 Page title: {scraper.driver.title}")
        
        # Check if we're on the right page
        if "emas" in current_url.lower() or "symbol" in current_url.lower():
            print("✅ Successfully on EMAS page!")
            
            # Perform infinite scroll
            print("🔄 Starting infinite scroll...")
            scroll_success = scraper._perform_infinite_scroll()
            
            if scroll_success:
                print("✅ Infinite scroll completed!")
                
                # Extract data
                print("📊 Extracting stream data...")
                comments = scraper._extract_stream_data()
                
                if comments:
                    print(f"✅ Found {len(comments)} comments!")
                    
                    # Add to data manager
                    scraper.data_manager.add_comments(comments)
                    
                    # Save data
                    output_file = scraper.save_data()
                    print(f"💾 Data saved to: {output_file}")
                    
                    # Show summary
                    summary = scraper.get_summary()
                    print(f"\n📈 Summary:")
                    print(f"   Total comments: {summary.get('total_comments', 0)}")
                    print(f"   Unique users: {summary.get('unique_users', 0)}")
                    print(f"   Total likes: {summary.get('total_likes', 0)}")
                    print(f"   Total replies: {summary.get('total_replies', 0)}")
                    
                    # Show sample comments
                    if scraper.data_manager.comments:
                        print(f"\n📝 Sample comments (first 3):")
                        for i, comment in enumerate(scraper.data_manager.comments[:3]):
                            print(f"   {i+1}. @{comment.username}: {comment.comment_text[:100]}...")
                            print(f"      Likes: {comment.likes}, Replies: {comment.replies}")
                            print()
                    
                    print("🎉 Scraping completed successfully!")
                else:
                    print("❌ No comments found")
            else:
                print("❌ Infinite scroll failed")
        else:
            print("❌ Not on EMAS page. Please make sure you're logged in and on the correct page.")
            print(f"Expected URL to contain 'emas' or 'symbol', got: {current_url}")
    
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if scraper.driver:
            input("\nPress Enter to close browser...")
            scraper.driver.quit()

if __name__ == "__main__":
    manual_login_scraper()