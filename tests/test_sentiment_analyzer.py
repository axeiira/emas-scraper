"""Tests for sentiment analysis module."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from emas_scraper.sentiment_analyzer import (
    AnalysisResult,
    IndonesianSentimentAnalyzer,
    NewsArticle,
    SentimentResult,
    analyze_news_sentiment,
    create_analysis_report,
    load_news_data
)


def test_sentiment_result_from_score():
    """Test SentimentResult creation from scores."""
    # Positive sentiment
    result = SentimentResult.from_score(0.8)
    assert result.label == "positive"
    assert result.score == 0.8
    assert result.confidence == "high"
    
    # Negative sentiment
    result = SentimentResult.from_score(-0.6)
    assert result.label == "negative"
    assert result.score == 0.6
    assert result.confidence == "medium"
    
    # Neutral sentiment
    result = SentimentResult.from_score(0.05)
    assert result.label == "neutral"
    assert result.score == 0.05
    assert result.confidence == "low"


def test_news_article():
    """Test NewsArticle dataclass."""
    article = NewsArticle(
        title="Test Title",
        url="https://example.com",
        source="Example.com",
        publication_date="2025-10-05"
    )
    
    assert article.title == "Test Title"
    assert article.url == "https://example.com"
    assert article.source == "Example.com"
    assert article.publication_date == "2025-10-05"


def test_load_news_data():
    """Test loading news data from JSON file."""
    test_data = [
        {
            "title": "Test News 1",
            "url": "https://example1.com",
            "source": "Source 1",
            "publication_date": "2025-10-05"
        },
        {
            "title": "Test News 2",
            "url": "https://example2.com",
            "source": "Source 2",
            "publication_date": "2025-10-04"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_path = Path(f.name)
    
    try:
        articles = load_news_data(temp_path)
        assert len(articles) == 2
        assert articles[0].title == "Test News 1"
        assert articles[1].url == "https://example2.com"
    finally:
        temp_path.unlink()


def test_load_news_data_invalid_file():
    """Test loading news data from non-existent file."""
    articles = load_news_data(Path("non_existent.json"))
    assert len(articles) == 0


@patch('transformers.AutoTokenizer')
@patch('transformers.AutoModelForSequenceClassification')
def test_indonesian_sentiment_analyzer_init_success(mock_model, mock_tokenizer):
    """Test successful initialization of Indonesian sentiment analyzer."""
    mock_tokenizer.from_pretrained.return_value = Mock()
    mock_model.from_pretrained.return_value = Mock()
    
    analyzer = IndonesianSentimentAnalyzer()
    assert analyzer.model_loaded is True
    assert analyzer.model is not None
    assert analyzer.tokenizer is not None


@patch('transformers.AutoTokenizer')
def test_indonesian_sentiment_analyzer_init_failure(mock_tokenizer):
    """Test fallback when Indonesian BERT fails to load."""
    mock_tokenizer.from_pretrained.side_effect = Exception("Model not found")
    
    analyzer = IndonesianSentimentAnalyzer()
    assert analyzer.model_loaded is False
    assert analyzer.model is None


def test_indonesian_sentiment_analyzer_textblob_fallback():
    """Test TextBlob fallback analysis."""
    with patch('transformers.AutoTokenizer') as mock_tokenizer:
        mock_tokenizer.from_pretrained.side_effect = Exception("Model not found")
        
        analyzer = IndonesianSentimentAnalyzer()
        
        with patch('textblob.TextBlob') as mock_textblob:
            mock_blob = Mock()
            mock_blob.sentiment.polarity = 0.7
            mock_textblob.return_value = mock_blob
            
            sentiment, method = analyzer.analyze_text("This is a positive text")
            
            assert method == "textblob_fallback"
            assert sentiment.label == "positive"
            assert sentiment.score == 0.7


def test_create_analysis_report():
    """Test creation of analysis report."""
    # Create test data
    articles = [
        NewsArticle("Positive News", "https://example1.com", "Source1", "2025-10-05"),
        NewsArticle("Negative News", "https://example2.com", "Source2", "2025-10-04"),
        NewsArticle("Neutral News", "https://example3.com", "Source3", "2025-10-03")
    ]
    
    results = [
        AnalysisResult(articles[0], SentimentResult("positive", 0.8, "high"), "bert"),
        AnalysisResult(articles[1], SentimentResult("negative", 0.7, "high"), "bert"),
        AnalysisResult(articles[2], SentimentResult("neutral", 0.3, "low"), "textblob")
    ]
    
    report = create_analysis_report(results, "test_file.json")
    
    # Check structure
    assert "analysis_metadata" in report
    assert "sentiment_summary" in report
    assert "detailed_results" in report
    
    # Check metadata
    assert report["analysis_metadata"]["total_articles"] == 3
    assert report["analysis_metadata"]["source_file"] == "test_file.json"
    
    # Check sentiment summary
    sentiment_summary = report["sentiment_summary"]["by_sentiment"]
    assert sentiment_summary["positive"] == 1
    assert sentiment_summary["negative"] == 1
    assert sentiment_summary["neutral"] == 1
    
    # Check percentages
    percentages = report["sentiment_summary"]["sentiment_percentages"]
    assert percentages["positive"] == 33.3
    assert percentages["negative"] == 33.3
    assert percentages["neutral"] == 33.3
    
    # Check detailed results
    detailed = report["detailed_results"]
    assert len(detailed) == 3
    assert detailed[0]["sentiment"]["label"] == "positive"
    assert detailed[1]["sentiment"]["label"] == "negative"
    assert detailed[2]["sentiment"]["label"] == "neutral"


def test_analyze_news_sentiment_integration():
    """Test the main analyze_news_sentiment function."""
    # Create test input file
    test_data = [
        {
            "title": "Great news for investors",
            "url": "https://example.com",
            "source": "Test Source",
            "publication_date": "2025-10-05"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_f:
        json.dump(test_data, input_f)
        input_path = Path(input_f.name)
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_f:
        output_path = Path(output_f.name)
    
    try:
        # Mock the sentiment analyzer to avoid loading actual models in tests
        with patch('emas_scraper.sentiment_analyzer.IndonesianSentimentAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_text.return_value = (
                SentimentResult("positive", 0.8, "high"),
                "mock_method"
            )
            mock_analyzer_class.return_value = mock_analyzer
            
            success = analyze_news_sentiment(input_path, output_path)
            
            assert success is True
            assert output_path.exists()
            
            # Check output file content
            with open(output_path, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            assert "analysis_metadata" in result_data
            assert "sentiment_summary" in result_data
            assert "detailed_results" in result_data
            assert len(result_data["detailed_results"]) == 1
            assert result_data["detailed_results"][0]["sentiment"]["label"] == "positive"
            
    finally:
        input_path.unlink()
        if output_path.exists():
            output_path.unlink()


def test_analyze_news_sentiment_no_input_file():
    """Test analyze_news_sentiment with non-existent input file."""
    input_path = Path("non_existent.json")
    output_path = Path("output.json")
    
    success = analyze_news_sentiment(input_path, output_path)
    assert success is False