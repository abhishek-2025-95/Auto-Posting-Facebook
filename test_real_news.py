#!/usr/bin/env python3
"""
Test if we're getting real breaking news
"""

from news_fetcher import get_trending_news, select_viral_topic

def test_real_news():
    print("="*60)
    print("TESTING REAL BREAKING NEWS")
    print("="*60)
    
    # Get articles
    articles = get_trending_news()
    print(f"\nFound {len(articles)} articles")
    
    if articles:
        print("\nFirst 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. TITLE: {article['title']}")
            print(f"   SOURCE: {article['source']}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"   DATE: {article.get('publishedAt', 'No date')}")
        
        # Test viral selection
        print(f"\n" + "="*40)
        print("VIRAL SELECTION:")
        print("="*40)
        
        viral_article = select_viral_topic(articles)
        print(f"\nSelected: {viral_article['title']}")
        print(f"Source: {viral_article['source']}")
        print(f"Reason: {viral_article.get('viral_reason', 'No reason')}")
        
        # Check if it's real news
        real_sources = ['CNN', 'BBC', 'Reuters', 'AP', 'NPR', 'Fox News', 'MSNBC', 'ABC', 'CBS', 'NBC', 'USA Today', 'Washington Post', 'New York Times']
        fallback_sources = ['TechNews', 'Financial Times', 'Global News']
        
        if viral_article['source'] in real_sources:
            print(f"\n✅ SUCCESS: Real breaking news from {viral_article['source']}")
        elif viral_article['source'] in fallback_sources:
            print(f"\n⚠️  FALLBACK: Using hardcoded content from {viral_article['source']}")
        else:
            print(f"\n❓ UNKNOWN: Source {viral_article['source']} not recognized")
    else:
        print("\n❌ No articles found - using fallback content")

if __name__ == "__main__":
    test_real_news()


