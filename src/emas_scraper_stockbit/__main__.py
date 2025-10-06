"""
Main module entry point for Stockbit Stream Scraper
"""

import sys
import os

# Add the current directory to Python path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .cli import main
except ImportError:
    # Fallback for direct execution
    from cli import main

if __name__ == "__main__":
    main()