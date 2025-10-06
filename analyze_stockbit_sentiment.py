#!/usr/bin/env python3
"""
Script to analyze sentiment of stockbit comments.
"""

from pathlib import Path
from src.emas_scraper.sentiment_analyzer import analyze_comments_sentiment

def main():
    """Main function to run sentiment analysis on stockbit comments."""
    
    # Define file paths
    input_csv = Path("src/stockbit_stream_EMAS.csv")
    output_csv = Path("sentiments.csv")
    
    # Check if input file exists
    if not input_csv.exists():
        print(f"❌ Input file not found: {input_csv}")
        return False
    
    print(f"🔍 Analyzing sentiment of comments from: {input_csv}")
    print(f"📊 Results will be saved to: {output_csv}")
    print("🚀 Starting analysis...")
    
    # Run sentiment analysis
    success = analyze_comments_sentiment(input_csv, output_csv)
    
    if success:
        print("✅ Sentiment analysis completed successfully!")
        return True
    else:
        print("❌ Sentiment analysis failed!")
        return False

if __name__ == "__main__":
    main()