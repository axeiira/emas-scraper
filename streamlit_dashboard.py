"""
Streamlit Dashboard for EMAS Sentiment Analysis Visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
from datetime import datetime, timedelta
import re
from collections import Counter
import numpy as np
import sys
import os

# Import our integrated sentiment analyzer
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'emas_scraper'))
from sentiment_analyzer import get_meaningful_words, STOCK_POSITIVE_TERMS, STOCK_NEGATIVE_TERMS

# Set page config
st.set_page_config(
    page_title="📊 Enhanced Stock Sentiment Dashboard",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .sentiment-positive {
        color: #28a745;
        font-weight: bold;
    }
    .sentiment-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: #6c757d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the sentiment data"""
    try:
        df = pd.read_csv('sentiments.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        return df
    except FileNotFoundError:
        st.error("sentiments.csv file not found. Please make sure the file exists in the project directory.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def extract_stock_symbols(text):
    """Extract stock symbols from text (e.g., $EMAS, $ANTM)"""
    if pd.isna(text):
        return []
    symbols = re.findall(r'\$([A-Z]{3,5})', str(text))
    return symbols

def create_enhanced_wordcloud(df, sentiment_filter=None):
    """Create word cloud with meaningful words only."""
    # Filter by sentiment if specified
    if sentiment_filter and sentiment_filter != "All":
        filtered_df = df[df['sentiment'].str.capitalize() == sentiment_filter.capitalize()]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return None
    
    # Combine all comment texts
    all_text = ' '.join(filtered_df['comment_text'].astype(str))
    
    # Get meaningful words using our enhancer
    meaningful_words = get_meaningful_words(all_text, min_length=3)
    
    if not meaningful_words:
        return None
    
    # Count word frequencies
    word_freq = Counter(meaningful_words)
    
    # Create color function based on sentiment
    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        if word.lower() in STOCK_POSITIVE_TERMS:
            return "green"
        elif word.lower() in STOCK_NEGATIVE_TERMS:
            return "red"
        elif word.isupper() and len(word) <= 4:  # Stock symbols
            return "blue"
        else:
            return "darkgray"
    
    # Generate word cloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        max_words=100,
        relative_scaling=0.5,
        color_func=color_func,
        font_path=None
    ).generate_from_frequencies(word_freq)
    
    return wordcloud

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Enhanced Stock Sentiment Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(df['date'].min(), df['date'].max()),
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )
    
    # Sentiment filter
    sentiment_filter = st.sidebar.multiselect(
        "Select Sentiments",
        options=df['sentiment'].unique(),
        default=df['sentiment'].unique()
    )
    
    # Filter data
    if len(date_range) == 2:
        filtered_df = df[
            (df['date'] >= date_range[0]) & 
            (df['date'] <= date_range[1]) &
            (df['sentiment'].isin(sentiment_filter))
        ]
    else:
        filtered_df = df[df['sentiment'].isin(sentiment_filter)]
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 Total Comments", 
            value=len(filtered_df)
        )
    
    with col2:
        positive_pct = (filtered_df['sentiment'] == 'Positive').mean() * 100
        st.metric(
            label="😊 Positive %", 
            value=f"{positive_pct:.1f}%"
        )
    
    with col3:
        negative_pct = (filtered_df['sentiment'] == 'Negative').mean() * 100
        st.metric(
            label="😞 Negative %", 
            value=f"{negative_pct:.1f}%"
        )
    
    with col4:
        neutral_pct = (filtered_df['sentiment'] == 'Neutral').mean() * 100
        st.metric(
            label="😐 Neutral %", 
            value=f"{neutral_pct:.1f}%"
        )
    
    # Charts section
    st.header("📈 Sentiment Analysis Charts")
    
    # Sentiment distribution pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Sentiment Distribution")
        sentiment_counts = filtered_df['sentiment'].value_counts()
        colors = {'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'}
        
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Overall Sentiment Distribution",
            color=sentiment_counts.index,
            color_discrete_map=colors
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📊 Sentiment Bar Chart")
        fig_bar = px.bar(
            x=sentiment_counts.index,
            y=sentiment_counts.values,
            title="Sentiment Count",
            color=sentiment_counts.index,
            color_discrete_map=colors,
            labels={'x': 'Sentiment', 'y': 'Count'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Time series analysis
    st.subheader("⏰ Sentiment Over Time")
    
    # Group by date and sentiment
    daily_sentiment = filtered_df.groupby(['date', 'sentiment']).size().reset_index(name='count')
    
    fig_timeline = px.line(
        daily_sentiment,
        x='date',
        y='count',
        color='sentiment',
        title="Daily Sentiment Trends",
        color_discrete_map=colors,
        labels={'date': 'Date', 'count': 'Number of Comments'}
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Hourly analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕐 Comments by Hour")
        hourly_data = filtered_df.groupby('hour').size().reset_index(name='count')
        
        fig_hourly = px.bar(
            hourly_data,
            x='hour',
            y='count',
            title="Comment Distribution by Hour of Day",
            labels={'hour': 'Hour of Day', 'count': 'Number of Comments'}
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        st.subheader("🕐 Sentiment by Hour")
        hourly_sentiment = filtered_df.groupby(['hour', 'sentiment']).size().reset_index(name='count')
        
        fig_hourly_sentiment = px.bar(
            hourly_sentiment,
            x='hour',
            y='count',
            color='sentiment',
            title="Hourly Sentiment Distribution",
            color_discrete_map=colors,
            labels={'hour': 'Hour of Day', 'count': 'Number of Comments'}
        )
        st.plotly_chart(fig_hourly_sentiment, use_container_width=True)
    
    # Stock symbols analysis
    st.header("💰 Stock Symbols Analysis")
    
    # Extract stock symbols
    filtered_df['stock_symbols'] = filtered_df['comment_text'].apply(extract_stock_symbols)
    
    # Flatten the list of symbols
    all_symbols = []
    for symbols in filtered_df['stock_symbols']:
        all_symbols.extend(symbols)
    
    if all_symbols:
        symbol_counts = Counter(all_symbols)
        top_symbols = dict(symbol_counts.most_common(10))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Mentioned Stocks")
            fig_stocks = px.bar(
                x=list(top_symbols.keys()),
                y=list(top_symbols.values()),
                title="Most Mentioned Stock Symbols",
                labels={'x': 'Stock Symbol', 'y': 'Mentions'}
            )
            st.plotly_chart(fig_stocks, use_container_width=True)
        
        with col2:
            st.subheader("📈 Stock Symbol Word Cloud")
            symbol_text = ' '.join([f"${symbol}" for symbol in all_symbols])
            if symbol_text:
                wordcloud_stocks = WordCloud(
                    width=400, 
                    height=300, 
                    background_color='white',
                    colormap='plasma'
                ).generate(symbol_text)
                
                fig_wc_stocks = plt.figure(figsize=(8, 6))
                plt.imshow(wordcloud_stocks, interpolation='bilinear')
                plt.axis('off')
                st.pyplot(fig_wc_stocks)
    
    # Enhanced Word Cloud Section
    st.header("☁️ Enhanced Word Cloud Analysis (Meaningful Words Only)")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        wordcloud_sentiment_filter = st.selectbox(
            "Word Cloud Sentiment Filter",
            ["All", "Positive", "Negative", "Neutral"],
            key="wordcloud_filter"
        )
    
    with col1:
        try:
            wordcloud = create_enhanced_wordcloud(filtered_df, wordcloud_sentiment_filter)
            if wordcloud:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                ax.set_title(f'Enhanced Word Cloud - {wordcloud_sentiment_filter} Sentiment', fontsize=16, pad=20)
                st.pyplot(fig)
                plt.close()
                
                st.info("🎨 **Color Legend:** Green = Positive stock terms, Red = Negative stock terms, Blue = Stock symbols, Gray = General terms")
            else:
                st.warning("No meaningful words found for the selected filter.")
        except Exception as e:
            st.error(f"Error creating word cloud: {e}")
    
    # Top Users Analysis
    st.header("👥 User Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Most Active Users")
        top_users = filtered_df['username'].value_counts().head(10)
        
        fig_users = px.bar(
            x=top_users.values,
            y=top_users.index,
            orientation='h',
            title="Top 10 Most Active Users",
            labels={'x': 'Number of Comments', 'y': 'Username'}
        )
        st.plotly_chart(fig_users, use_container_width=True)
    
    with col2:
        st.subheader("😊 User Sentiment Distribution")
        user_sentiment = filtered_df.groupby(['username', 'sentiment']).size().reset_index(name='count')
        top_users_list = filtered_df['username'].value_counts().head(5).index
        user_sentiment_top = user_sentiment[user_sentiment['username'].isin(top_users_list)]
        
        fig_user_sentiment = px.bar(
            user_sentiment_top,
            x='username',
            y='count',
            color='sentiment',
            title="Sentiment Distribution - Top 5 Users",
            color_discrete_map=colors
        )
        fig_user_sentiment.update_xaxes(tickangle=45)
        st.plotly_chart(fig_user_sentiment, use_container_width=True)
    
    # Stock-Specific Enhancement Analysis Section
    st.header("🏛️ Stock-Specific Enhancement Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Show stock terms analysis if columns exist
        if 'stock_terms_found' in filtered_df.columns:
            stock_comments = filtered_df[filtered_df['stock_terms_found'].notna() & (filtered_df['stock_terms_found'] != '')]
            
            if not stock_comments.empty:
                st.subheader("🔍 Stock Terms Analysis")
                st.metric(
                    "Comments with Stock Terms",
                    len(stock_comments),
                    f"{len(stock_comments)/len(filtered_df)*100:.1f}% of total"
                )
                
                # Show most common stock terms
                all_terms = []
                for terms_str in stock_comments['stock_terms_found'].dropna():
                    if terms_str:
                        all_terms.extend([term.strip() for term in terms_str.split(',') if term.strip()])
                
                if all_terms:
                    term_counts = Counter(all_terms)
                    st.write("**Most Common Stock Terms:**")
                    for term, count in term_counts.most_common(5):
                        st.write(f"• {term}: {count} times")
            else:
                st.info("No stock-specific terms detected in comments.")
        else:
            st.info("Stock terms analysis not available. Please run enhanced sentiment analysis.")
    
    with col2:
        # Show enhancement impact if columns exist
        if 'original_sentiment' in filtered_df.columns:
            changed_comments = filtered_df[
                (filtered_df['original_sentiment'].notna()) & 
                (filtered_df['original_sentiment'] != '') & 
                (filtered_df['original_sentiment'].str.capitalize() != filtered_df['sentiment'])
            ]
            
            if not changed_comments.empty:
                st.subheader("🔄 Sentiment Enhancement Impact")
                st.metric(
                    "Comments Adjusted",
                    len(changed_comments),
                    f"{len(changed_comments)/len(filtered_df)*100:.1f}% of total"
                )
                
                # Show adjustment patterns
                adjustment_patterns = changed_comments.groupby(['original_sentiment', 'sentiment']).size().reset_index(name='count')
                
                if not adjustment_patterns.empty:
                    st.write("**Adjustment Patterns:**")
                    for _, row in adjustment_patterns.iterrows():
                        st.write(f"• {row['original_sentiment']} → {row['sentiment']}: {row['count']} comments")
            else:
                st.info("No sentiment adjustments were made by the stock-specific enhancement.")
        else:
            st.info("Enhancement impact analysis not available. Please run enhanced sentiment analysis.")
    
    # Sample Comments Section
    st.header("💬 Sample Comments")
    
    sentiment_tabs = st.tabs(["😊 Positive", "😞 Negative", "😐 Neutral"])
    
    for i, sentiment in enumerate(['Positive', 'Negative', 'Neutral']):
        with sentiment_tabs[i]:
            sentiment_comments = filtered_df[filtered_df['sentiment'] == sentiment].head(10)
            
            if not sentiment_comments.empty:
                for _, comment in sentiment_comments.iterrows():
                    timestamp_str = comment['timestamp']
                    if hasattr(comment['timestamp'], 'strftime'):
                        timestamp_str = comment['timestamp'].strftime('%Y-%m-%d %H:%M')
                    
                    confidence_info = ""
                    if 'confidence' in comment and comment['confidence']:
                        confidence_info = f" - {comment['confidence']} confidence"
                    
                    with st.expander(f"@{comment['username']} - {timestamp_str}{confidence_info}"):
                        st.write(comment['comment_text'])
                        
                        # Show enhanced information if available
                        if 'stock_terms_found' in comment and comment['stock_terms_found']:
                            st.caption(f"🏛️ Stock terms: {comment['stock_terms_found']}")
                        
                        if 'original_sentiment' in comment and comment['original_sentiment'] and comment['original_sentiment'] != comment['sentiment']:
                            st.caption(f"🔄 Original sentiment: {comment['original_sentiment']} → Enhanced: {comment['sentiment']}")
            else:
                st.info(f"No {sentiment.lower()} comments found in the selected date range.")
    
    # Summary Statistics
    st.header("📋 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Basic Stats")
        st.write(f"**Total Comments:** {len(filtered_df):,}")
        st.write(f"**Unique Users:** {filtered_df['username'].nunique():,}")
        st.write(f"**Date Range:** {filtered_df['date'].min()} to {filtered_df['date'].max()}")
        
    with col2:
        st.subheader("💭 Comment Length Stats")
        comment_lengths = filtered_df['comment_text'].str.len()
        st.write(f"**Average Length:** {comment_lengths.mean():.1f} characters")
        st.write(f"**Median Length:** {comment_lengths.median():.1f} characters")
        st.write(f"**Max Length:** {comment_lengths.max()} characters")
    
    with col3:
        st.subheader("🎯 Sentiment Summary")
        for sentiment in ['Positive', 'Negative', 'Neutral']:
            count = len(filtered_df[filtered_df['sentiment'] == sentiment])
            percentage = (count / len(filtered_df)) * 100
            st.write(f"**{sentiment}:** {count:,} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()