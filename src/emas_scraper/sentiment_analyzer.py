"""Sentiment analysis module for Indonesian news articles and comments with integrated stock enhancement."""

from __future__ import annotations

import csv
import json
import logging
import pandas as pd
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Indonesian stopwords and common filler words
INDONESIAN_STOPWORDS = {
    'dan', 'yang', 'di', 'ke', 'dari', 'dalam', 'untuk', 'pada', 'dengan', 'adalah', 'ini', 'itu', 
    'juga', 'akan', 'atau', 'dapat', 'sudah', 'belum', 'masih', 'ada', 'tidak', 'bukan', 'ya', 
    'saya', 'kamu', 'dia', 'kita', 'mereka', 'kami', 'kalian', 'anda', 'nya', 'mu', 'ku',
    'tapi', 'namun', 'tetapi', 'karena', 'sebab', 'jadi', 'maka', 'lalu', 'kemudian',
    'ga', 'gak', 'yg', 'dgn', 'dg', 'sm', 'sama', 'bgt', 'banget', 'dong', 'sih', 'kok',
    'udah', 'udh', 'dah', 'aja', 'aj', 'jg', 'juga', 'kl', 'kalo', 'kalau', 'klo',
    'tp', 'trs', 'terus', 'lgi', 'lagi', 'lg', 'gmn', 'gimana', 'bgm', 'bagaimana',
    'sm', 'sama', 'gt', 'gitu', 'gini', 'begini', 'begitu', 'kayak', 'kyk', 'seperti',
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
}

# Stock-specific sentiment indicators
STOCK_POSITIVE_TERMS = {
    # Price movement terms
    'naik': 2.0, 'up': 2.0, 'bullish': 2.5, 'rally': 2.5, 'breakout': 2.5,
    'pump': 2.0, 'moon': 3.0, 'rocket': 2.5, 'surge': 2.0, 'spike': 2.0,
    'roket': 2.5, 'terbang': 2.0, 'meluncur': 2.0, 'meroket': 2.5,
    
    # Profit terms
    'profit': 2.0, 'untung': 2.0, 'cuan': 2.5, 'gain': 2.0, 'jackpot': 3.0,
    'money': 1.5, 'duit': 1.5, 'kaya': 2.0, 'tajir': 2.5,
    
    # Positive emotions
    'mantap': 2.0, 'keren': 1.5, 'bagus': 1.5, 'solid': 2.0, 'top': 2.0,
    'gokil': 2.0, 'dahsyat': 2.5, 'luar biasa': 2.5, 'amazing': 2.0,
    'excellent': 2.0, 'perfect': 2.5, 'good': 1.5, 'great': 2.0,
    
    # Trading terms
    'buy': 1.5, 'beli': 1.5, 'hold': 1.0, 'accumulate': 2.0, 'akumulasi': 2.0,
    'strong buy': 2.5, 'recommended': 2.0, 'target': 1.5,
    
    # Stock specific positive terms
    'ara': 2.0,  # Auto Rejection Atas (max price reached)
    'auto reject atas': 2.0, 'auto rejection atas': 2.0,
    'limit up': 2.5, 'suspend naik': 2.5,
    'volume gede': 1.5, 'volume besar': 1.5, 'high volume': 1.5,
    'support kuat': 2.0, 'strong support': 2.0,
    'golden cross': 2.5, 'breakout resistance': 2.5,
    
    # Emojis and symbols
    '🚀': 2.5, '🌙': 2.5, '💰': 2.0, '📈': 2.0, '💎': 2.0, '🔥': 2.0,
    '👍': 1.5, '😍': 2.0, '🤑': 2.5, '💪': 2.0, '⬆️': 2.0, '↗️': 2.0
}

STOCK_NEGATIVE_TERMS = {
    # Price movement terms
    'turun': -2.0, 'down': -2.0, 'bearish': -2.5, 'crash': -3.0, 'dump': -2.5,
    'drop': -2.0, 'fall': -2.0, 'decline': -2.0, 'correction': -1.5,
    'anjlok': -2.5, 'terjun': -2.5, 'ambruk': -3.0, 'jebol': -2.5,
    
    # Loss terms
    'loss': -2.0, 'rugi': -2.0, 'loss': -2.0, 'bangkrut': -3.0, 'minus': -2.0,
    'cut loss': -2.5, 'cutloss': -2.5, 'stop loss': -1.5,
    
    # Negative emotions
    'jelek': -1.5, 'buruk': -2.0, 'parah': -2.5, 'hancur': -3.0, 'bad': -2.0,
    'terrible': -2.5, 'awful': -2.5, 'worst': -3.0, 'sucks': -2.5,
    'sedih': -1.5, 'kecewa': -2.0, 'frustasi': -2.0,
    
    # Trading terms
    'sell': -1.5, 'jual': -1.5, 'exit': -1.0, 'weak': -1.5, 'lemah': -1.5,
    'resistance kuat': -1.5, 'strong resistance': -1.5,
    
    # Stock specific negative terms
    'arb': -2.0,  # Auto Rejection Bawah (min price reached)
    'auto reject bawah': -2.0, 'auto rejection bawah': -2.0,
    'limit down': -2.5, 'suspend turun': -2.5,
    'volume kecil': -1.0, 'volume sepi': -1.5, 'low volume': -1.0,
    'support jebol': -2.5, 'break support': -2.5,
    'death cross': -2.5, 'breakdown support': -2.5,
    
    # Emojis and symbols
    '📉': -2.0, '😭': -2.0, '😢': -1.5, '💔': -2.0, '😞': -1.5,
    '👎': -1.5, '😡': -2.0, '🤬': -2.5, '⬇️': -2.0, '↘️': -2.0
}


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
class Comment:
    """Comment data structure for stockbit stream."""
    username: str
    timestamp: str
    comment_text: str
    likes: int
    replies: int
    post_id: str


@dataclass
class AnalysisResult:
    """Complete sentiment analysis result."""
    article: NewsArticle
    sentiment: SentimentResult
    method: str  # 'indonesian_bert', 'textblob_fallback'


@dataclass
class EnhancedSentimentResult:
    """Enhanced sentiment result with stock-specific adjustments."""
    original_label: str
    original_score: float
    stock_adjusted_label: str
    stock_adjusted_score: float
    confidence: str
    stock_terms_found: List[str]
    adjustment_reason: str


@dataclass
class CommentAnalysisResult:
    """Complete sentiment analysis result for comments."""
    comment: Comment
    sentiment: SentimentResult
    method: str  # 'indonesian_bert', 'textblob_fallback'
    enhanced_sentiment: Optional[EnhancedSentimentResult] = None


class IndonesianSentimentAnalyzer:
    """Indonesian sentiment analyzer using BERT or TextBlob fallback with integrated stock enhancement."""
    
    def __init__(self, use_stock_enhancement: bool = True):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.use_stock_enhancement = use_stock_enhancement
        self.positive_terms = STOCK_POSITIVE_TERMS
        self.negative_terms = STOCK_NEGATIVE_TERMS
        self.stopwords = INDONESIAN_STOPWORDS
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
    
    def analyze_text(self, text: str) -> Tuple[SentimentResult, str, Optional[EnhancedSentimentResult]]:
        """Analyze sentiment of text using BERT or TextBlob fallback with integrated stock enhancement."""
        # Get base sentiment analysis
        if self.model_loaded and self.model is not None:
            sentiment, method = self._analyze_with_bert(text)
        else:
            sentiment, method = self._analyze_with_textblob(text)
        
        # Apply stock-specific enhancement if enabled
        enhanced_sentiment = None
        if self.use_stock_enhancement:
            enhanced_sentiment = self.enhance_sentiment(
                sentiment.label, sentiment.score, text
            )
            
            # Update the main sentiment result with enhanced values
            sentiment = SentimentResult(
                label=enhanced_sentiment.stock_adjusted_label,
                score=enhanced_sentiment.stock_adjusted_score,
                confidence=enhanced_sentiment.confidence
            )
        
        return sentiment, method, enhanced_sentiment
    
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
            label_map = {0: "Positive", 1: "Neutral", 2: "Negative"}
            predicted_label = label_map[predictions.item()]
            confidence_score = torch.max(probabilities).item()
            
            # Convert to our standard format
            if predicted_label == "Positive":
                final_score = confidence_score
            elif predicted_label == "Negative":
                final_score = -confidence_score
            else:  # Neutral
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
    
    def clean_text_for_wordcloud(self, text: str) -> str:
        """Clean text by removing stopwords and non-meaningful words."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs, mentions, hashtags
        text = re.sub(r'http\S+|www\S+|@\w+|#\w+', '', text)
        
        # Remove stock symbols like $EMAS, $ANTM etc but keep the symbol for context
        text = re.sub(r'\$([A-Z]{3,4})', r'\1', text)
        
        # Remove punctuation except emojis
        text = re.sub(r'[^\w\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', ' ', text)
        
        # Split into words and filter stopwords
        words = text.split()
        filtered_words = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def find_stock_terms(self, text: str) -> Tuple[List[str], float]:
        """Find stock-specific terms and calculate sentiment adjustment."""
        text_lower = text.lower()
        found_positive = []
        found_negative = []
        total_adjustment = 0.0
        
        # Check for positive terms
        for term, weight in self.positive_terms.items():
            if term in text_lower:
                found_positive.append(term)
                total_adjustment += weight
        
        # Check for negative terms
        for term, weight in self.negative_terms.items():
            if term in text_lower:
                found_negative.append(term)
                total_adjustment += weight  # weight is already negative
        
        all_found = found_positive + found_negative
        return all_found, total_adjustment
    
    def enhance_sentiment(self, original_label: str, original_score: float, text: str) -> EnhancedSentimentResult:
        """Enhance sentiment analysis with stock-specific knowledge."""
        stock_terms, adjustment = self.find_stock_terms(text)
        
        # Convert original label to score for calculation
        if original_label.lower() == 'positive':
            base_score = original_score
        elif original_label.lower() == 'negative':
            base_score = -original_score
        else:  # neutral
            base_score = 0.0
        
        # Apply stock-specific adjustment
        adjusted_score = base_score + (adjustment * 0.3)  # Scale adjustment to not overwhelm original
        
        # Determine new label
        if adjusted_score > 0.2:
            new_label = 'positive'
        elif adjusted_score < -0.2:
            new_label = 'negative'
        else:
            new_label = 'neutral'
        
        # Determine confidence based on presence of stock terms
        if stock_terms:
            if abs(adjusted_score) > 0.8:
                confidence = 'high'
            elif abs(adjusted_score) > 0.4:
                confidence = 'medium'
            else:
                confidence = 'low'
        else:
            # Use original confidence logic
            if abs(adjusted_score) >= 0.7:
                confidence = 'high'
            elif abs(adjusted_score) >= 0.4:
                confidence = 'medium'
            else:
                confidence = 'low'
        
        # Create adjustment reason
        if stock_terms:
            adjustment_reason = f"Found stock terms: {', '.join(stock_terms[:3])}{'...' if len(stock_terms) > 3 else ''}"
        else:
            adjustment_reason = "No stock-specific terms found"
        
        return EnhancedSentimentResult(
            original_label=original_label,
            original_score=original_score,
            stock_adjusted_label=new_label,
            stock_adjusted_score=abs(adjusted_score),
            confidence=confidence,
            stock_terms_found=stock_terms,
            adjustment_reason=adjustment_reason
        )


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


def load_comments_data(file_path: Path) -> List[Comment]:
    """Load comments from CSV file."""
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        
        comments = []
        for _, row in df.iterrows():
            comment = Comment(
                username=str(row['username']),
                timestamp=str(row['timestamp']),
                comment_text=str(row['comment_text']),
                likes=int(row['likes']) if pd.notna(row['likes']) else 0,
                replies=int(row['replies']) if pd.notna(row['replies']) else 0,
                post_id=str(row['post_id'])
            )
            comments.append(comment)
        
        logger.info(f"Loaded {len(comments)} comments from {file_path}")
        return comments
        
    except Exception as e:
        logger.error(f"Failed to load comments data from {file_path}: {e}")
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


def analyze_comments_sentiment_batch(comments: List[Comment]) -> List[CommentAnalysisResult]:
    """Analyze sentiment for a batch of comments with stock enhancement."""
    analyzer = IndonesianSentimentAnalyzer(use_stock_enhancement=True)
    results = []
    
    logger.info(f"Starting enhanced sentiment analysis for {len(comments)} comments...")
    
    for i, comment in enumerate(comments, 1):
        if i % 100 == 0:  # Log progress every 100 comments
            logger.info(f"Analyzing comment {i}/{len(comments)}")
        
        try:
            # Use comment_text for sentiment analysis
            sentiment, method, enhanced_sentiment = analyzer.analyze_text(comment.comment_text)
            
            result = CommentAnalysisResult(
                comment=comment,
                sentiment=sentiment,
                method=method,
                enhanced_sentiment=enhanced_sentiment
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to analyze comment {i}: {e}")
            # Add error result
            error_sentiment = SentimentResult(label="neutral", score=0.0, confidence="low")
            result = CommentAnalysisResult(
                comment=comment,
                sentiment=error_sentiment,
                method="error",
                enhanced_sentiment=None
            )
            results.append(result)
    
    logger.info(f"Enhanced sentiment analysis completed for {len(results)} comments")
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


def save_comments_sentiment_csv(results: List[CommentAnalysisResult], output_file: Path) -> None:
    """Save comment sentiment analysis results to CSV file with enhanced information."""
    try:
        # Prepare data for CSV
        csv_data = []
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        enhanced_count = 0
        
        for result in results:
            # Capitalize sentiment label for consistency
            sentiment_label = result.sentiment.label.capitalize()
            sentiment_counts[sentiment_label] += 1
            
            # Prepare enhanced information
            stock_terms = ""
            original_sentiment = ""
            adjustment_reason = ""
            
            if result.enhanced_sentiment:
                enhanced_count += 1
                stock_terms = ", ".join(result.enhanced_sentiment.stock_terms_found[:3])  # Top 3 terms
                original_sentiment = result.enhanced_sentiment.original_label.capitalize()
                adjustment_reason = result.enhanced_sentiment.adjustment_reason
            
            csv_data.append({
                'username': result.comment.username,
                'timestamp': result.comment.timestamp,
                'comment_text': result.comment.comment_text,
                'sentiment': sentiment_label,
                'confidence': result.sentiment.confidence,
                'original_sentiment': original_sentiment,
                'stock_terms_found': stock_terms,
                'adjustment_reason': adjustment_reason,
                'analysis_method': result.method
            })
        
        # Write to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"Enhanced sentiment analysis results saved to {output_file}")
        
        # Print summary
        total = len(results)
        print(f"\n📊 Enhanced Comment Sentiment Analysis Summary:")
        print(f"Total Comments: {total}")
        print(f"Positive: {sentiment_counts['Positive']} ({round((sentiment_counts['Positive'] / total) * 100, 1)}%)")
        print(f"Negative: {sentiment_counts['Negative']} ({round((sentiment_counts['Negative'] / total) * 100, 1)}%)")
        print(f"Neutral: {sentiment_counts['Neutral']} ({round((sentiment_counts['Neutral'] / total) * 100, 1)}%)")
        print(f"Comments with stock-specific adjustments: {enhanced_count} ({round((enhanced_count / total) * 100, 1)}%)")
        print(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to save sentiment analysis CSV: {e}")


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


def analyze_comments_sentiment(input_csv: Path, output_csv: Path) -> bool:
    """Main function to analyze sentiment of comments from stockbit stream CSV."""
    try:
        # Load comments data
        comments = load_comments_data(input_csv)
        if not comments:
            logger.error("No comments to analyze")
            return False
        
        # Analyze sentiment
        results = analyze_comments_sentiment_batch(comments)
        if not results:
            logger.error("Sentiment analysis failed")
            return False
        
        # Save results to CSV
        save_comments_sentiment_csv(results, output_csv)
        
        return True
        
    except Exception as e:
        logger.error(f"Comment sentiment analysis failed: {e}")
        return False


def get_meaningful_words(text: str, min_length: int = 3) -> List[str]:
    """Extract meaningful words from text for word cloud."""
    analyzer = IndonesianSentimentAnalyzer(use_stock_enhancement=False)  # Just for text cleaning
    cleaned_text = analyzer.clean_text_for_wordcloud(text)
    
    # Additional filtering for meaningful words
    words = cleaned_text.split()
    meaningful_words = []
    
    for word in words:
        if len(word) >= min_length:
            # Keep stock symbols, company names, and meaningful terms
            if (word.isupper() and len(word) <= 4) or \
               word in STOCK_POSITIVE_TERMS or \
               word in STOCK_NEGATIVE_TERMS or \
               (word.isalpha() and len(word) >= 4):
                meaningful_words.append(word)
    
    return meaningful_words