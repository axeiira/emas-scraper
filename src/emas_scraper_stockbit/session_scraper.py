"""
Browser Session Reuse Scraper - connects to existing Chrome session
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import StockbitConfig
from scraper import StockbitScraper
import time
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def session_reuse_scraper():
    """
    Scraper that connects to an existing Chrome browser session
    """
    
    # Load config
    config = StockbitConfig.from_ini_file()
    
    print("🔧 BROWSER SESSION REUSE MODE")
    print("=" * 50)
    print("Please follow these steps:")
    print()
    print("STEP 1: Close all Chrome windows first")
    print()
    print("STEP 2: Open Chrome with debugging enabled:")
    print('   Windows: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
    print("   (Copy and paste this command in a new Command Prompt)")
    print()
    print("STEP 3: In the Chrome window that opens:")
    print("   - Go to https://stockbit.com/login")
    print("   - Log in with your credentials")
    print("   - Navigate to https://stockbit.com/symbol/EMAS")
    print("   - Verify you can see the Stream section")
    print("   - Keep this browser open")
    print()
    
    input("Press Enter when you're logged in and on the EMAS page...")
    
    print("\n🚀 Connecting to your existing browser session...")
    
    try:
        # Connect to existing Chrome session
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Create driver that connects to existing session
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Connected to existing browser session!")
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        # Check if we're on the right page
        current_url = driver.current_url
        if "emas" in current_url.lower() or ("stockbit.com/symbol" in current_url.lower()):
            print("✅ You're on the correct page!")
            
            # Create scraper instance and assign our connected driver
            scraper = StockbitScraper(config)
            scraper.driver = driver
            
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
            print("❌ Please navigate to the EMAS page in your browser first")
            print(f"Current URL: {current_url}")
            print("Expected URL to contain 'emas' or 'stockbit.com/symbol'")
    
    except Exception as e:
        print(f"💥 Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome is running with --remote-debugging-port=9222")
        print("2. Make sure no other programs are using Chrome")
        print("3. Try closing all Chrome windows and starting fresh")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\nPress Enter to finish (your browser will stay open)...")
        # Don't quit the driver since it's the user's browser

if __name__ == "__main__":
    session_reuse_scraper()