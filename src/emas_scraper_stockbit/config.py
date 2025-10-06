"""
Configuration file for Stockbit Stream Scraper
"""

import os
import configparser
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class StockbitConfig:
    """Configuration class for Stockbit scraper"""
    
    # Login credentials
    username: str = "YOUR_USERNAME_HERE"
    password: str = "YOUR_PASSWORD_HERE"
    
    # URLs
    login_url: str = "https://stockbit.com/login"
    base_url: str = "https://stockbit.com"
    
    # Target symbol (default: EMAS)
    symbol: str = "EMAS"
    
    # Selenium settings
    headless: bool = False
    implicit_wait: int = 10
    page_load_timeout: int = 30
    
    # Scrolling settings
    scroll_pause_time: float = 3.0
    max_scrolls: int = 100
    scroll_increment: int = 1000
    
    # Data collection limits
    target_data_count: int = 10000
    no_new_data_limit: int = 5
    
    # Output settings
    output_format: str = "csv"  # csv, json
    output_filename: Optional[str] = None
    
    def __post_init__(self):
        if self.output_filename is None:
            self.output_filename = f"stockbit_stream_{self.symbol}.{self.output_format}"
    
    @property
    def symbol_url(self) -> str:
        """Get the full URL for the symbol page"""
        return f"{self.base_url}/symbol/{self.symbol}"
    
    def validate_credentials(self) -> bool:
        """Validate that credentials are provided"""
        invalid_usernames = ["YOUR_USERNAME_HERE", "MASUKKAN_USERNAME_ANDA"]
        invalid_passwords = ["YOUR_PASSWORD_HERE", "MASUKKAN_PASSWORD_ANDA"]
        
        return (self.username not in invalid_usernames and 
                self.password not in invalid_passwords and
                self.username and self.password)
    
    @classmethod
    def from_ini_file(cls, config_path: Optional[str] = None) -> 'StockbitConfig':
        """Load configuration from INI file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.ini"
        
        if not os.path.exists(config_path):
            # Return default config
            return cls()
        
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Load credentials
        username = config.get('credentials', 'username', fallback='YOUR_USERNAME_HERE')
        password = config.get('credentials', 'password', fallback='YOUR_PASSWORD_HERE')
        
        # Load scraping settings
        symbol = config.get('scraping', 'symbol', fallback='EMAS')
        headless = config.getboolean('scraping', 'headless', fallback=False)
        implicit_wait = config.getint('scraping', 'implicit_wait', fallback=10)
        page_load_timeout = config.getint('scraping', 'page_load_timeout', fallback=30)
        scroll_pause_time = config.getfloat('scraping', 'scroll_pause_time', fallback=3.0)
        max_scrolls = config.getint('scraping', 'max_scrolls', fallback=100)
        target_data_count = config.getint('scraping', 'target_data_count', fallback=10000)
        no_new_data_limit = config.getint('scraping', 'no_new_data_limit', fallback=5)
        
        # Load output settings
        output_format = config.get('output', 'format', fallback='csv')
        output_filename = config.get('output', 'filename', fallback=None)
        if output_filename == '':
            output_filename = None
        
        return cls(
            username=username,
            password=password,
            symbol=symbol,
            headless=headless,
            implicit_wait=implicit_wait,
            page_load_timeout=page_load_timeout,
            scroll_pause_time=scroll_pause_time,
            max_scrolls=max_scrolls,
            target_data_count=target_data_count,
            no_new_data_limit=no_new_data_limit,
            output_format=output_format,
            output_filename=output_filename
        )