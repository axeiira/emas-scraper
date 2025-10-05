"""Sentiment analysis module for Indonesian news articles."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result for a single article."""
    label: str  # 'positive', 'negative', 'neutral'
    score: float  # confidence score 0-1
    confidence: str  # 'high', 'medium', 'low'
    
    @classmethod
    def from_score(cls, score: float, threshold_high: float = 0.7, threshold_low: float = 0.4) -> "SentimentResult":
        """Create SentimentResult from a score between -1 and 1."""
        # Determine label
        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        # Convert to absolute confidence score
        abs_score = abs(score)
        
        # Determine confidence level
        if abs_score >= threshold_high:
            confidence = "high"
        elif abs_score >= threshold_low:
            confidence = "medium"
        else:
            confidence = "low"
        
        return cls(label=label, score=abs_score, confidence=confidence)


@dataclass
class NewsArticle:
    """News article data structure."""
    title: str
    url: str
    source: Optional[str]
    publication_date: Optional[str]


@dataclass
class AnalysisResult:
    """Complete sentiment analysis result."""
    article: NewsArticle
    sentiment: SentimentResult
    method: str  # 'indonesian_bert', 'textblob_fallback'


class IndonesianSentimentAnalyzer:
    """Indonesian sentiment analyzer using BERT or TextBlob fallback."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Indonesian BERT model with fallback handling."""
        try:
            logger.info("Loading Indonesian BERT model...")
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            model_name = "ayameRushia/bert-base-indonesian-1.5G-sentiment-analysis-smsa"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model_loaded = True
            logger.info("Indonesian BERT model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load Indonesian BERT model: {e}")
            logger.info("Will use TextBlob fallback for sentiment analysis")
            self.model_loaded = False
    
    def analyze_text(self, text: str) -> Tuple[SentimentResult, str]:
        """Analyze sentiment of text using BERT or TextBlob fallback."""
        if self.model_loaded and self.model is not None:
            return self._analyze_with_bert(text)
        else:
            return self._analyze_with_textblob(text)
    
    def _analyze_with_bert(self, text: str) -> Tuple[SentimentResult, str]:
        """Analyze sentiment using Indonesian BERT."""
        try:
            import torch
            import torch.nn.functional as F
            
            # Tokenize input text (truncate if too long)
            text_truncated = text[:512]  # BERT max length
            inputs = self.tokenizer(text_truncated, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=-1)
                probabilities = F.softmax(outputs.logits, dim=-1)
            
            # Label mapping based on the model specification
            label_map = {0: "Positif", 1: "Netral", 2: "Negatif"}
            predicted_label = label_map[predictions.item()]
            confidence_score = torch.max(probabilities).item()
            
            # Convert to our standard format
            if predicted_label == "Positif":
                final_score = confidence_score
            elif predicted_label == "Negatif":
                final_score = -confidence_score
            else:  # Netral
                final_score = 0.0
            
            sentiment = SentimentResult.from_score(final_score)
            return sentiment, "indonesian_bert"
            
        except Exception as e:
            logger.warning(f"BERT analysis failed: {e}, falling back to TextBlob")
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Tuple[SentimentResult, str]:
        """Analyze sentiment using TextBlob as fallback."""
        try:
            from textblob import TextBlob
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            sentiment = SentimentResult.from_score(polarity)
            return sentiment, "textblob_fallback"
            
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {e}")
            # Return neutral as last resort
            sentiment = SentimentResult(label="neutral", score=0.0, confidence="low")
            return sentiment, "error_fallback"


def load_news_data(file_path: Path) -> List[NewsArticle]:
    """Load news articles from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = []
        for item in data:
            article = NewsArticle(
                title=item.get('title', ''),
                url=item.get('url', ''),
                source=item.get('source'),
                publication_date=item.get('publication_date')
            )
            articles.append(article)
        
        logger.info(f"Loaded {len(articles)} articles from {file_path}")
        return articles
        
    except Exception as e:
        logger.error(f"Failed to load news data from {file_path}: {e}")
        return []


def analyze_sentiment_batch(articles: List[NewsArticle]) -> List[AnalysisResult]:
    """Analyze sentiment for a batch of articles."""
    analyzer = IndonesianSentimentAnalyzer()
    results = []
    
    logger.info(f"Starting sentiment analysis for {len(articles)} articles...")
    
    for i, article in enumerate(articles, 1):
        logger.info(f"Analyzing article {i}/{len(articles)}: {article.title[:50]}...")
        
        try:
            # Use title for sentiment analysis (most important part)
            sentiment, method = analyzer.analyze_text(article.title)
            
            result = AnalysisResult(
                article=article,
                sentiment=sentiment,
                method=method
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to analyze article {i}: {e}")
            # Add error result
            error_sentiment = SentimentResult(label="neutral", score=0.0, confidence="low")
            result = AnalysisResult(
                article=article,
                sentiment=error_sentiment,
                method="error"
            )
            results.append(result)
    
    logger.info(f"Sentiment analysis completed for {len(results)} articles")
    return results


def create_analysis_report(results: List[AnalysisResult], source_file: str) -> Dict:
    """Create comprehensive analysis report."""
    # Count sentiments
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    method_counts = {}
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    
    analysis_data = []
    
    for result in results:
        # Count sentiments
        sentiment_counts[result.sentiment.label] += 1
        
        # Count methods
        method_counts[result.method] = method_counts.get(result.method, 0) + 1
        
        # Count confidence levels
        confidence_counts[result.sentiment.confidence] += 1
        
        # Add to analysis data
        analysis_data.append({
            "title": result.article.title,
            "url": result.article.url,
            "source": result.article.source,
            "publication_date": result.article.publication_date,
            "sentiment": {
                "label": result.sentiment.label,
                "score": round(result.sentiment.score, 3),
                "confidence": result.sentiment.confidence
            },
            "analysis_method": result.method
        })
    
    # Create comprehensive report
    report = {
        "analysis_metadata": {
            "analysis_date": datetime.now().isoformat(),
            "source_file": source_file,
            "total_articles": len(results),
            "analysis_methods_used": method_counts
        },
        "sentiment_summary": {
            "by_sentiment": sentiment_counts,
            "by_confidence": confidence_counts,
            "sentiment_percentages": {
                label: round((count / len(results)) * 100, 1) 
                for label, count in sentiment_counts.items()
            }
        },
        "detailed_results": analysis_data
    }
    
    return report


def save_analysis_report(report: Dict, output_file: Path) -> None:
    """Save analysis report to JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Analysis report saved to {output_file}")
        
        # Print summary
        summary = report["sentiment_summary"]["by_sentiment"]
        total = report["analysis_metadata"]["total_articles"]
        
        print(f"\n📊 Sentiment Analysis Summary:")
        print(f"Total Articles: {total}")
        print(f"Positive: {summary['positive']} ({report['sentiment_summary']['sentiment_percentages']['positive']}%)")
        print(f"Negative: {summary['negative']} ({report['sentiment_summary']['sentiment_percentages']['negative']}%)")
        print(f"Neutral: {summary['neutral']} ({report['sentiment_summary']['sentiment_percentages']['neutral']}%)")
        
    except Exception as e:
        logger.error(f"Failed to save analysis report: {e}")


def analyze_news_sentiment(input_file: Path, output_file: Path) -> bool:
    """Main function to analyze sentiment of news articles."""
    try:
        # Load news data
        articles = load_news_data(input_file)
        if not articles:
            logger.error("No articles to analyze")
            return False
        
        # Analyze sentiment
        results = analyze_sentiment_batch(articles)
        if not results:
            logger.error("Sentiment analysis failed")
            return False
        
        # Create and save report
        report = create_analysis_report(results, str(input_file))
        save_analysis_report(report, output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return False