#!/usr/bin/env python3
"""
Test script to check if we're getting real breaking news or fallback content
"""

from news_fetcher import get_trending_news, select_viral_topic
from datetime import datetime

def test_news_sources():
    """Test what news sources we're actually getting"""
    print("="*60)
    print("TESTING NEWS SOURCES - REAL vs FALLBACK")
    print("="*60)
    
    # Test 1: Get raw articles
    print("\n1. Fetching articles from news API...")
    articles = get_trending_news()
    
    print(f"\nFound {len(articles)} articles:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. TITLE: {article['title']}")
        print(f"   SOURCE: {article['source']}")
        print(f"   URL: {article.get('url', 'No URL')}")
        print(f"   PUBLISHED: {article.get('publishedAt', 'No date')}")
        print(f"   DESCRIPTION: {article['description'][:100]}...")
    
    # Test 2: Check if we're getting real news or fallback
    print(f"\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    
    # Check for fallback indicators
    fallback_sources = ['TechNews', 'Financial Times', 'Global News']
    real_sources = ['CNN', 'BBC', 'Reuters', 'AP', 'NPR', 'Fox News', 'MSNBC', 'ABC', 'CBS', 'NBC']
    
    real_news_count = 0
    fallback_count = 0
    
    for article in articles:
        source = article['source']
        if source in fallback_sources:
            fallback_count += 1
            print(f"⚠️  FALLBACK: {article['title']} (Source: {source})")
        elif source in real_sources:
            real_news_count += 1
            print(f"✅ REAL NEWS: {article['title']} (Source: {source})")
        else:
            print(f"❓ UNKNOWN: {article['title']} (Source: {source})")
    
    print(f"\nSUMMARY:")
    print(f"Real news articles: {real_news_count}")
    print(f"Fallback articles: {fallback_count}")
    print(f"Unknown sources: {len(articles) - real_news_count - fallback_count}")
    
    if fallback_count > 0:
        print(f"\n⚠️  WARNING: Using fallback content - News API may be failing")
        print(f"   This means you're NOT getting the latest breaking news")
    else:
        print(f"\n✅ SUCCESS: Getting real breaking news from live sources")
    
    # Test 3: Viral selection
    print(f"\n" + "="*60)
    print("VIRAL SELECTION TEST:")
    print("="*60)
    
    if articles:
        viral_article = select_viral_topic(articles)
        print(f"\nSelected viral topic:")
        print(f"Title: {viral_article['title']}")
        print(f"Source: {viral_article['source']}")
        print(f"Viral reason: {viral_article.get('viral_reason', 'No reason provided')}")
        
        # Check if selected article is real or fallback
        if viral_article['source'] in fallback_sources:
            print(f"\n⚠️  SELECTED FALLBACK CONTENT - Not real breaking news!")
        else:
            print(f"\n✅ SELECTED REAL BREAKING NEWS")
    else:
        print("No articles to analyze")

if __name__ == "__main__":
    test_news_sources()


