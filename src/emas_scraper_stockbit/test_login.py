"""
Quick test to verify login selectors work with actual Stockbit HTML
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import StockbitConfig
from scraper import StockbitScraper

def test_login_only():
    """Test just the login process with detailed logging"""
    
    # Load config
    config = StockbitConfig.from_ini_file()
    
    if not config.validate_credentials():
        print("❌ Please configure credentials in config.ini")
        return
    
    print(f"🔧 Testing login for user: {config.username}")
    print(f"🔧 Login URL: {config.login_url}")
    
    # Create scraper
    scraper = StockbitScraper(config)
    
    try:
        # Initialize driver
        scraper.driver = scraper._init_driver()
        print("✅ WebDriver initialized")
        
        # Test login only
        login_success = scraper._login()
        
        if login_success:
            print("✅ Login successful!")
            print(f"📍 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
            
            # Wait a bit to see if we can stay logged in
            import time
            time.sleep(5)
            
            print(f"📍 URL after 5 seconds: {scraper.driver.current_url}")
        else:
            print("❌ Login failed")
            print(f"📍 Current URL: {scraper.driver.current_url}")
            print(f"📄 Page title: {scraper.driver.title}")
    
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if scraper.driver:
            input("Press Enter to close browser...")
            scraper.driver.quit()

if __name__ == "__main__":
    test_login_only()