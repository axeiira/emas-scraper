"""
Stockbit Stream Scraper - Main scraper implementation
"""

import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

try:
    from .config import StockbitConfig
    from .models import StreamComment, StreamDataManager
except ImportError:
    from config import StockbitConfig
    from models import StreamComment, StreamDataManager


class StockbitScraper:
    """Main scraper class for Stockbit Stream data"""
    
    def __init__(self, config: StockbitConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.data_manager = StreamDataManager()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver with proper options"""
        chrome_options = Options()
        
        if self.config.headless:
            chrome_options.add_argument("--headless")
        
        # Anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set realistic user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Additional stealth options
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Create driver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            # Fallback to system Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
        
        # Execute anti-detection scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Set timeouts
        driver.implicitly_wait(self.config.implicit_wait)
        driver.set_page_load_timeout(self.config.page_load_timeout)
        
        # Maximize window
        driver.maximize_window()
        
        self.logger.info("Chrome WebDriver initialized successfully")
        
        return driver
    
    def _login(self) -> bool:
        """Perform login to Stockbit"""
        try:
            self.logger.info("Starting login process...")
            self.driver.get(self.config.login_url)
            
            # Wait for page to load completely
            time.sleep(3)
            self.logger.info(f"Current URL after loading login page: {self.driver.current_url}")
            
            # Wait for login form to load
            wait = WebDriverWait(self.driver, 15)
            
            # Log page title for debugging
            self.logger.info(f"Page title: {self.driver.title}")
            
            # Find username/email field (based on actual Stockbit HTML)
            username_selectors = [
                "#username",  # Primary selector from HTML
                "input[data-cy='login-form-username']",  # Data attribute selector
                "input[placeholder='Email or username']",  # Exact placeholder match
                "input[name='email']",  # Fallback
                "input[name='username']",  # Fallback
                "input[type='email']",  # Fallback
            ]
            
            username_field = None
            found_selector = None
            for selector in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    found_selector = selector
                    self.logger.info(f"Found username field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                self.logger.error("Could not find username/email field")
                # Log all input elements for debugging
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                self.logger.error(f"Found {len(inputs)} input elements on page")
                for i, inp in enumerate(inputs[:5]):  # Log first 5 inputs
                    try:
                        self.logger.error(f"Input {i}: name='{inp.get_attribute('name')}', type='{inp.get_attribute('type')}', placeholder='{inp.get_attribute('placeholder')}'")
                    except:
                        pass
                return False
            
            # Find password field (based on actual Stockbit HTML)
            password_selectors = [
                "#password",  # Primary selector from HTML
                "input[data-cy='login-form-pw']",  # Data attribute selector
                "input[name='password']",  # Name attribute
                "input[type='password']",  # Type fallback
                "input[placeholder='Password']"  # Exact placeholder match
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found password field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                self.logger.error("Could not find password field")
                return False
            
            # Enter credentials with human-like typing
            self.logger.info("Entering username...")
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(self.config.username)
            
            self.logger.info("Entering password...")
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(self.config.password)
            
            # Wait a bit before clicking submit
            time.sleep(1)
            
            # Find and click login button (based on actual Stockbit HTML)
            login_selectors = [
                "#email-login-button",  # Primary selector from HTML
                "button[data-cy='login-form-submit']",  # Data attribute selector
                "button[type='submit']",  # Type fallback
                "button.ant-btn-primary",  # Ant Design primary button
                ".ant-btn.ant-btn-primary",  # Ant Design with classes
                "form button[type='submit']"  # Form submit button fallback
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found login button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                self.logger.error("Could not find login button")
                # Log all buttons for debugging
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                self.logger.error(f"Found {len(buttons)} button elements on page")
                for i, btn in enumerate(buttons[:3]):
                    try:
                        self.logger.error(f"Button {i}: text='{btn.text}', type='{btn.get_attribute('type')}', class='{btn.get_attribute('class')}'")
                    except:
                        pass
                return False
            
            self.logger.info("Clicking login button...")
            login_button.click()
            
            # Wait for login to complete with longer timeout
            self.logger.info("Waiting for login to complete...")
            time.sleep(8)
            
            # Check if login was successful by looking for URL change
            current_url = self.driver.current_url
            self.logger.info(f"Current URL after login attempt: {current_url}")
            
            # Check multiple indicators of successful login
            login_success_indicators = [
                "login" not in current_url.lower(),
                "dashboard" in current_url.lower(),
                "home" in current_url.lower(),
                "profile" in current_url.lower(),
                "trusted-device" in current_url.lower()  # This also indicates successful login
            ]
            
            # Check for presence of logged-in user indicators
            try:
                # Look for common post-login elements in Stockbit
                login_success_elements = [
                    ".user-menu",
                    ".profile-menu", 
                    "[data-testid='user-menu']",
                    ".ant-dropdown-trigger",  # Ant Design dropdown (likely user menu)
                    ".avatar",
                    ".user-avatar",
                    "img[alt*='avatar']",
                    "img[alt*='profile']"
                ]
                
                for selector in login_success_elements:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        self.logger.info(f"Found post-login element: {selector} - login successful!")
                        return True
                    except NoSuchElementException:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error checking for post-login indicators: {e}")
            
            # Handle trusted device prompt if present
            if "trusted-device" in current_url.lower():
                self.logger.info("Detected trusted device prompt - attempting to handle...")
                return self._handle_trusted_device_prompt()
            
            if any(login_success_indicators):
                self.logger.info("Login successful based on URL change!")
                return True
            else:
                self.logger.error("Login failed - still on login page or no success indicators found")
                self.logger.error(f"Page title after login: {self.driver.title}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed with error: {str(e)}")
            return False
    
    def _handle_trusted_device_prompt(self) -> bool:
        """Handle the trusted device security prompt"""
        try:
            self.logger.info("Handling trusted device prompt...")
            
            # Wait a bit for the page to load
            time.sleep(3)
            
            # Look for common trusted device buttons
            trusted_device_selectors = [
                "button:contains('Trust this device')",
                "button:contains('Trust Device')", 
                "button:contains('Yes')",
                "button:contains('Continue')",
                "button:contains('Skip')",
                ".trust-device-button",
                ".continue-button",
                "#trust-device",
                "[data-cy*='trust']",
                "[data-cy*='continue']",
                "button[type='submit']"
            ]
            
            # Try to find and click a continue/trust button
            for selector in trusted_device_selectors:
                try:
                    if "contains" in selector:
                        # Handle text-based selectors
                        text = selector.split("'")[1]
                        xpath = f"//button[contains(text(), '{text}')]"
                        button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    self.logger.info(f"Found trusted device button with selector: {selector}")
                    button.click()
                    
                    # Wait for navigation
                    time.sleep(5)
                    
                    current_url = self.driver.current_url
                    self.logger.info(f"URL after handling trusted device: {current_url}")
                    
                    # Check if we're no longer on the trusted device page
                    if "trusted-device" not in current_url.lower():
                        self.logger.info("Successfully handled trusted device prompt!")
                        return True
                    
                except (NoSuchElementException, Exception) as e:
                    continue
            
            # If no button found, try to skip by navigating directly to symbol page
            self.logger.warning("Could not find trusted device button, attempting to navigate directly...")
            self.driver.get(self.config.symbol_url)
            time.sleep(5)
            
            current_url = self.driver.current_url
            if "symbol" in current_url.lower() or "emas" in current_url.lower():
                self.logger.info("Successfully bypassed trusted device prompt by direct navigation!")
                return True
            
            self.logger.error("Failed to handle trusted device prompt")
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling trusted device prompt: {e}")
            return False
                
        except Exception as e:
            self.logger.error(f"Login failed with error: {str(e)}")
            return False
    
    def _navigate_to_symbol(self) -> bool:
        """Navigate to the target symbol page"""
        try:
            self.logger.info(f"Navigating to symbol page: {self.config.symbol}")
            self.driver.get(self.config.symbol_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 15)
            
            # Look for stream section or any indicator that the page loaded
            stream_indicators = [
                ".stream-container",
                ".stream-section", 
                "[data-testid='stream']",
                ".post-container",
                ".comment-container"
            ]
            
            for indicator in stream_indicators:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, indicator)))
                    self.logger.info("Symbol page loaded successfully")
                    return True
                except TimeoutException:
                    continue
            
            # If no specific stream indicators found, just wait a bit and assume success
            time.sleep(3)
            self.logger.info("Navigated to symbol page (stream section detection inconclusive)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to symbol page: {str(e)}")
            return False
    
    def _perform_infinite_scroll(self) -> bool:
        """Perform intelligent scrolling until target data count or no new data"""
        try:
            self.logger.info(f"Starting infinite scroll process (target: {self.config.target_data_count} comments)...")
            
            scroll_count = 0
            no_new_data_count = 0
            last_data_count = 0
            
            while scroll_count < self.config.max_scrolls:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(self.config.scroll_pause_time)
                
                # Extract current data and count
                current_comments = self._extract_stream_data()
                current_data_count = len(current_comments)
                
                # Update data manager with current data
                self.data_manager.comments = current_comments
                
                # Check if we've reached target data count
                if current_data_count >= self.config.target_data_count:
                    self.logger.info(f"Target data count reached: {current_data_count}/{self.config.target_data_count}")
                    break
                
                # Check if no new data was loaded
                if current_data_count == last_data_count:
                    no_new_data_count += 1
                    self.logger.info(f"No new data found (attempt {no_new_data_count}/{self.config.no_new_data_limit})")
                    
                    if no_new_data_count >= self.config.no_new_data_limit:
                        self.logger.info("No new data available, stopping scroll")
                        break
                    
                    # Try scrolling a bit more for stubborn content
                    self.driver.execute_script(f"window.scrollBy(0, {self.config.scroll_increment});")
                    time.sleep(self.config.scroll_pause_time)
                else:
                    no_new_data_count = 0
                    scroll_count += 1
                    new_data = current_data_count - last_data_count
                    self.logger.info(f"Scroll {scroll_count}: Found {new_data} new comments (total: {current_data_count})")
                    last_data_count = current_data_count
            
            final_count = len(self.data_manager.comments)
            self.logger.info(f"Infinite scroll completed after {scroll_count} scrolls with {final_count} comments")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during infinite scroll: {str(e)}")
            return False
    
    def _extract_timestamp(self, timestamp_text: str) -> Optional[datetime]:
        """Extract and parse timestamp from text, handling Indonesian date format"""
        if not timestamp_text:
            return None
        
        try:
            timestamp_text = timestamp_text.strip()
            original_text = timestamp_text
            timestamp_text_lower = timestamp_text.lower()
            
            # Handle relative timestamps (e.g., "2h ago", "1d ago")
            if "ago" in timestamp_text_lower:
                if "h" in timestamp_text_lower:  # hours ago
                    match = re.search(r'(\d+)h', timestamp_text_lower)
                    if match:
                        hours = int(match.group(1))
                        return datetime.now() - pd.Timedelta(hours=hours)
                elif "d" in timestamp_text_lower:  # days ago
                    match = re.search(r'(\d+)d', timestamp_text_lower)
                    if match:
                        days = int(match.group(1))
                        return datetime.now() - pd.Timedelta(days=days)
                elif "min" in timestamp_text_lower:  # minutes ago
                    match = re.search(r'(\d+)', timestamp_text_lower)
                    if match:
                        minutes = int(match.group(1))
                        return datetime.now() - pd.Timedelta(minutes=minutes)
            
            # Handle absolute timestamps like "6 Oct 25, 13:20"
            patterns = [
                # Pattern for "6 Oct 25, 13:20" format (Indonesian Stockbit format)
                r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des|Oct|Aug|Dec)\s+(\d{2})[,\s]+(\d{1,2}):(\d{2})',
                # Standard English patterns
                r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{2,4})[,\s]+(\d{1,2}):(\d{2})',
                r'(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{2})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})',
            ]
            
            # Month mapping for both English and Indonesian
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Mei': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Agu': 8, 'Sep': 9, 'Oct': 10, 'Okt': 10, 
                'Nov': 11, 'Dec': 12, 'Des': 12
            }
            
            for pattern in patterns:
                match = re.search(pattern, timestamp_text, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) >= 5 and groups[1].isalpha():  # Month name pattern
                            day, month_str, year_str, hour, minute = groups
                            
                            month = month_map.get(month_str.capitalize())
                            if not month:
                                continue
                                
                            year = int(year_str)
                            # Handle 2-digit year (assume 2000s)
                            if year < 100:
                                year += 2000
                            
                            return datetime(year, month, int(day), int(hour), int(minute))
                            
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Error parsing timestamp {original_text}: {e}")
                        continue
            
            # If no pattern matched, return current time as fallback
            self.logger.debug(f"Could not parse timestamp, using current time: {original_text}")
            return datetime.now()
            
        except Exception as e:
            self.logger.debug(f"Exception parsing timestamp {timestamp_text}: {e}")
            return datetime.now()
    
    def _extract_stream_data(self) -> List[StreamComment]:
        """Extract stream comments from the loaded page"""
        try:
            self.logger.info("Extracting stream data from page...")
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            comments = []
            
            # Updated selectors based on actual Stockbit HTML structure
            post_selectors = [
                'div[data-cy*="stream-post-symbol"]',  # Primary selector from actual HTML
                '.sc-ad32df5c-8',  # Class from actual HTML
                'div[data-cy*="stream-post"]',  # More general data-cy selector
                '.stream-post',  # Fallback
                '.post-item',  # Fallback
            ]
            
            posts = []
            for selector in post_selectors:
                posts = soup.select(selector)
                if posts:
                    self.logger.info(f"Found {len(posts)} posts using selector: {selector}")
                    break
            
            if not posts:
                # Try more generic approach
                self.logger.warning("No posts found with specific selectors, trying data-cy pattern...")
                posts = soup.find_all('div', {'data-cy': re.compile(r'stream-post')})
                
            if not posts:
                # Final fallback: look for divs with stream-related classes
                self.logger.warning("Still no posts found, trying class-based fallback...")
                posts = soup.find_all(['div'], class_=re.compile(r'sc-ad32df5c-8|ebbJkf', re.I))
            
            for post in posts:
                try:
                    comment_data = self._extract_single_comment(post)
                    if comment_data:
                        comments.append(comment_data)
                except Exception as e:
                    self.logger.warning(f"Error extracting single comment: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(comments)} comments")
            return comments
            
        except Exception as e:
            self.logger.error(f"Error extracting stream data: {str(e)}")
            return []
    
    def _extract_single_comment(self, post_element) -> Optional[StreamComment]:
        """Extract data from a single post/comment element based on actual Stockbit HTML"""
        try:
            # Extract post ID from data-cy attribute
            post_id = ""
            data_cy = post_element.get('data-cy', '')
            if 'stream-post-symbol-' in data_cy:
                post_id = data_cy.replace('stream-post-symbol-', '')
            
            # Extract username - based on actual HTML structure
            username = ""
            # Look for the profile link pattern: a[href*="/username"]
            username_link = post_element.select_one('a[href*="/"][href$="?source=2"]')
            if username_link:
                href = username_link.get('href', '')
                # Extract username from href like "/adityassatriaa?source=2"
                if href.startswith('/') and '?' in href:
                    username = href.split('?')[0][1:]  # Remove leading '/' and query params
            
            if not username:
                # Fallback: look for username in link classes
                username_elem = post_element.select_one('.sc-ad32df5c-3.kvgQrd')
                if username_elem:
                    username = username_elem.get_text(strip=True)
            
            # Extract comment text - look for the main content paragraph
            comment_text = ""
            # Based on HTML structure: look for p tag in content area
            content_selectors = [
                '.sc-7f9f3cba-1.gVgfuQ',  # Specific class from HTML
                '.sc-8a078c1d-0.sc-7f9f3cba-1',  # More general pattern
                'p[style*="overflow-wrap"]',  # Paragraph with specific style
                '.sc-ad32df5c-5 p',  # Paragraph inside content container
                'p'  # Final fallback
            ]
            
            for selector in content_selectors:
                content_elem = post_element.select_one(selector)
                if content_elem:
                    comment_text = content_elem.get_text(strip=True)
                    if comment_text:  # Only break if we found actual text
                        break
            
            # Extract timestamp - look for the post link with timestamp
            timestamp = None
            timestamp_selectors = [
                'a[href*="/post/"] .sc-ad32df5c-3.iVkFTS',  # Specific timestamp class
                'a[href*="/post/"]',  # Post link
                '.ljSlgm.iVkFTS',  # Timestamp class pattern
            ]
            
            for selector in timestamp_selectors:
                time_elem = post_element.select_one(selector)
                if time_elem:
                    timestamp_text = time_elem.get_text(strip=True)
                    if timestamp_text and any(char.isdigit() for char in timestamp_text):
                        timestamp = self._extract_timestamp(timestamp_text)
                        break
            
            # Extract likes count - look for likes info
            likes = 0
            like_selectors = [
                '.likes-info',  # Based on HTML class
                '.sc-8a078c1d-0.iLZqZP',  # Specific likes class
                '[data-cy*="like"]',  # Data attribute
            ]
            
            for selector in like_selectors:
                like_elem = post_element.select_one(selector)
                if like_elem:
                    like_text = like_elem.get_text(strip=True)
                    if like_text:
                        likes = self._extract_number(like_text)
                        break
            
            # Extract replies/comments count - look for comment icon area
            replies = 0
            reply_selectors = [
                '[data-cy="company-stream-comment-icon"]',  # Based on HTML
                '.lkviPX',  # Class near comment icon
                'img[alt="Icon Comment New"]',  # Comment icon
            ]
            
            # Look for text near comment icon that might contain count
            for selector in reply_selectors:
                reply_elem = post_element.select_one(selector)
                if reply_elem:
                    # Check parent/sibling elements for count text
                    parent = reply_elem.parent
                    if parent:
                        reply_text = parent.get_text(strip=True)
                        if reply_text and any(char.isdigit() for char in reply_text):
                            replies = self._extract_number(reply_text)
                            break
            
            # Only create comment if we have essential data
            if username or comment_text:
                comment = StreamComment(
                    username=username,
                    comment_text=comment_text,
                    timestamp=timestamp,
                    likes=likes,
                    replies=replies,
                    post_id=post_id
                )
                
                self.logger.debug(f"Extracted comment: {username} - {comment_text[:50]}...")
                return comment
            
            self.logger.debug(f"Skipping post - no username or comment text found")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting single comment: {str(e)}")
            return None
    
    def _extract_number(self, text: str) -> int:
        """Extract number from text (handles 1.2K, 1M format)"""
        if not text:
            return 0
        
        try:
            # Remove non-digit characters except K, M, decimal point
            clean_text = re.sub(r'[^\d.KM]', '', text.upper())
            
            if 'K' in clean_text:
                number = float(clean_text.replace('K', ''))
                return int(number * 1000)
            elif 'M' in clean_text:
                number = float(clean_text.replace('M', ''))
                return int(number * 1000000)
            else:
                # Try to extract just the number
                numbers = re.findall(r'\d+', clean_text)
                return int(numbers[0]) if numbers else 0
                
        except Exception:
            return 0
    
    def scrape(self) -> bool:
        """Main scraping method"""
        try:
            # Validate credentials
            if not self.config.validate_credentials():
                self.logger.error("Invalid credentials. Please set STOCKBIT_USERNAME and STOCKBIT_PASSWORD environment variables or update config.")
                return False
            
            # Initialize driver
            self.driver = self._init_driver()
            
            # Perform login
            if not self._login():
                return False
            
            # Navigate to symbol page
            if not self._navigate_to_symbol():
                return False
            
            # Perform infinite scroll
            if not self._perform_infinite_scroll():
                return False
            
            # Extract data
            comments = self._extract_stream_data()
            
            if not comments:
                self.logger.warning("No comments extracted")
                return False
            
            # Add to data manager
            self.data_manager.add_comments(comments)
            
            self.logger.info(f"Scraping completed successfully! Collected {len(comments)} comments")
            return True
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_data(self, filename: Optional[str] = None) -> str:
        """Save scraped data to file"""
        if filename is None:
            filename = self.config.output_filename
        
        if self.config.output_format.lower() == 'json':
            return self.data_manager.save_to_json(filename)
        else:
            return self.data_manager.save_to_csv(filename)
    
    def scrape_session_mode(self) -> bool:
        """Session reuse scraping method (connects to existing Chrome session)"""
        try:
            # Connect to existing Chrome session
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Connected to existing browser session")
            
            current_url = self.driver.current_url
            self.logger.info(f"Current URL: {current_url}")
            
            # Check if we're on the right page
            if self.config.symbol.lower() not in current_url.lower() and "symbol" not in current_url.lower():
                self.logger.error("Not on the expected symbol page. Please navigate to the EMAS page in your browser.")
                return False
            
            # Perform infinite scroll
            if not self._perform_infinite_scroll():
                return False
            
            # Extract data
            comments = self._extract_stream_data()
            
            if not comments:
                self.logger.warning("No comments extracted")
                return False
            
            # Add to data manager
            self.data_manager.add_comments(comments)
            
            self.logger.info(f"Session scraping completed successfully! Collected {len(comments)} comments")
            return True
            
        except Exception as e:
            self.logger.error(f"Session scraping failed: {str(e)}")
            self.logger.error("Make sure Chrome is running with --remote-debugging-port=9222")
            return False
        
        finally:
            # Don't quit the driver in session mode since it's the user's browser
            pass
    
    def scrape_manual_mode(self) -> bool:
        """Manual scraping method (assumes user is already logged in)"""
        try:
            # Initialize driver
            self.driver = self._init_driver()
            
            # Navigate directly to symbol page (user should already be logged in)
            self.logger.info(f"Navigating to symbol page: {self.config.symbol}")
            self.driver.get(self.config.symbol_url)
            
            # Wait for page to load
            time.sleep(5)
            
            current_url = self.driver.current_url
            self.logger.info(f"Current URL: {current_url}")
            
            # Check if we're on the right page
            if self.config.symbol.lower() not in current_url.lower() and "symbol" not in current_url.lower():
                self.logger.error("Not on the expected symbol page. Please make sure you're logged in.")
                return False
            
            # Perform infinite scroll
            if not self._perform_infinite_scroll():
                return False
            
            # Extract data
            comments = self._extract_stream_data()
            
            if not comments:
                self.logger.warning("No comments extracted")
                return False
            
            # Add to data manager
            self.data_manager.add_comments(comments)
            
            self.logger.info(f"Manual scraping completed successfully! Collected {len(comments)} comments")
            return True
            
        except Exception as e:
            self.logger.error(f"Manual scraping failed: {str(e)}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of scraped data"""
        return self.data_manager.get_summary()