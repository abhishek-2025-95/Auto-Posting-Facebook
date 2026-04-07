#!/usr/bin/env python3
"""
Enhanced News Fetcher - Multiple sources for viral breaking news
Combines Reddit, Google News, and other sources for maximum viral potential
"""

from reddit_news_fetcher import get_reddit_viral_news, select_reddit_viral_topic
from google_news_fetcher import get_google_news_viral, select_google_viral_topic
from datetime import datetime
import json

def get_all_viral_sources():
    """
    Get viral news from multiple sources and combine them
    This gives us the best of all worlds for viral content
    """
    print("="*60)
    print("FETCHING VIRAL NEWS FROM MULTIPLE SOURCES")
    print("="*60)
    
    all_articles = []
    
    # Source 1: Reddit (best for real viral engagement)
    print("\n1. Fetching from Reddit...")
    try:
        reddit_posts = get_reddit_viral_news()
        if reddit_posts:
            # Convert Reddit posts to standard format
            for post in reddit_posts:
                all_articles.append({
                    'title': post['title'],
                    'description': post['description'],
                    'url': post['url'],
                    'source': post['source'],
                    'publishedAt': post['publishedAt'],
                    'engagement': post.get('engagement', 0),
                    'platform': 'Reddit',
                    'subreddit': post.get('subreddit', ''),
                    'score': post.get('score', 0),
                    'comments': post.get('comments', 0)
                })
            print(f"✅ Reddit: {len(reddit_posts)} viral posts")
        else:
            print("❌ Reddit: No posts found")
    except Exception as e:
        print(f"❌ Reddit error: {e}")
    
    # Source 2: Google News (best for breaking news)
    print("\n2. Fetching from Google News...")
    try:
        google_articles = get_google_news_viral()
        if google_articles:
            # Convert Google News to standard format
            for article in google_articles:
                all_articles.append({
                    'title': article['title'],
                    'description': article['title'],  # Use title as description
                    'url': article['url'],
                    'source': article['source'],
                    'publishedAt': article['publishedAt'],
                    'engagement': 0,  # Google News doesn't have engagement metrics
                    'platform': 'Google News',
                    'subreddit': '',
                    'score': 0,
                    'comments': 0
                })
            print(f"✅ Google News: {len(google_articles)} articles")
        else:
            print("❌ Google News: No articles found")
    except Exception as e:
        print(f"❌ Google News error: {e}")
    
    # Source 3: Enhanced fallback with viral topics
    print("\n3. Adding enhanced fallback content...")
    fallback_articles = get_enhanced_fallback_news()
    for article in fallback_articles:
        all_articles.append(article)
    print(f"✅ Fallback: {len(fallback_articles)} viral topics")
    
    print(f"\n📊 TOTAL: {len(all_articles)} articles from all sources")
    return all_articles

def get_enhanced_fallback_news():
    """Enhanced fallback with more viral topics"""
    return [
        {
            'title': 'BREAKING: Major Data Breach Exposes Millions of Americans',
            'description': 'Shocking security failure leaves personal information vulnerable in what experts call the largest breach of 2024',
            'url': 'https://example.com/tech-breach',
            'source': 'CNN',
            'publishedAt': datetime.now().isoformat(),
            'engagement': 50000,
            'platform': 'Fallback',
            'subreddit': '',
            'score': 25000,
            'comments': 25000
        },
        {
            'title': 'URGENT: Economic Crisis Deepens as Inflation Hits Record High',
            'description': 'Central banks scramble to address unprecedented economic challenges affecting millions of families',
            'url': 'https://example.com/economy-crisis',
            'source': 'Reuters',
            'publishedAt': datetime.now().isoformat(),
            'engagement': 45000,
            'platform': 'Fallback',
            'subreddit': '',
            'score': 20000,
            'comments': 25000
        },
        {
            'title': 'EXCLUSIVE: Climate Summit Ends in Major Controversy',
            'description': 'World leaders clash over environmental policies as global temperatures continue to rise dramatically',
            'url': 'https://example.com/climate-summit',
            'source': 'BBC',
            'publishedAt': datetime.now().isoformat(),
            'engagement': 40000,
            'platform': 'Fallback',
            'subreddit': '',
            'score': 18000,
            'comments': 22000
        },
        {
            'title': 'SHOCKING: New Study Reveals Hidden Health Crisis',
            'description': 'Groundbreaking research exposes concerning trends that could affect millions of Americans',
            'url': 'https://example.com/health-study',
            'source': 'NPR',
            'publishedAt': datetime.now().isoformat(),
            'engagement': 35000,
            'platform': 'Fallback',
            'subreddit': '',
            'score': 15000,
            'comments': 20000
        },
        {
            'title': 'BREAKING: Major Political Scandal Rocks Washington',
            'description': 'Exclusive investigation reveals shocking details that could change everything',
            'url': 'https://example.com/political-scandal',
            'source': 'Washington Post',
            'publishedAt': datetime.now().isoformat(),
            'engagement': 60000,
            'platform': 'Fallback',
            'subreddit': '',
            'score': 30000,
            'comments': 30000
        }
    ]

def select_best_viral_topic(all_articles):
    """
    Select the best viral topic from all sources
    Prioritizes Reddit engagement data when available
    """
    print("\n" + "="*40)
    print("SELECTING BEST VIRAL TOPIC")
    print("="*40)
    
    if not all_articles:
        print("No articles available")
        return None
    
    # Separate Reddit posts (have engagement data) from other sources
    reddit_posts = [article for article in all_articles if article['platform'] == 'Reddit']
    other_articles = [article for article in all_articles if article['platform'] != 'Reddit']
    
    # If we have Reddit posts, use Reddit selection (best engagement data)
    if reddit_posts:
        print(f"Using Reddit data ({len(reddit_posts)} posts) for viral selection...")
        return select_reddit_viral_topic(reddit_posts)
    
    # Otherwise use Google News selection
    elif other_articles:
        print(f"Using Google News data ({len(other_articles)} articles) for viral selection...")
        return select_google_viral_topic(other_articles)
    
    # Final fallback
    else:
        print("Using fallback content...")
        return all_articles[0]

def test_enhanced_news_system():
    """Test the enhanced multi-source news system"""
    print("="*60)
    print("TESTING ENHANCED MULTI-SOURCE NEWS SYSTEM")
    print("="*60)
    
    # Get articles from all sources
    all_articles = get_all_viral_sources()
    
    if all_articles:
        print(f"\n📈 SOURCE BREAKDOWN:")
        reddit_count = len([a for a in all_articles if a['platform'] == 'Reddit'])
        google_count = len([a for a in all_articles if a['platform'] == 'Google News'])
        fallback_count = len([a for a in all_articles if a['platform'] == 'Fallback'])
        
        print(f"   Reddit: {reddit_count} posts")
        print(f"   Google News: {google_count} articles")
        print(f"   Fallback: {fallback_count} topics")
        
        # Show top articles from each source
        print(f"\n🔥 TOP ARTICLES BY SOURCE:")
        
        # Reddit top posts
        reddit_posts = [a for a in all_articles if a['platform'] == 'Reddit']
        if reddit_posts:
            print(f"\n   REDDIT TOP POSTS:")
            for i, post in enumerate(reddit_posts[:3], 1):
                print(f"   {i}. {post['title'][:50]}... (Score: {post['score']})")
        
        # Google News top articles
        google_articles = [a for a in all_articles if a['platform'] == 'Google News']
        if google_articles:
            print(f"\n   GOOGLE NEWS TOP ARTICLES:")
            for i, article in enumerate(google_articles[:3], 1):
                print(f"   {i}. {article['title'][:50]}...")
        
        # Select best viral topic
        viral_topic = select_best_viral_topic(all_articles)
        
        if viral_topic:
            print(f"\n🎯 SELECTED VIRAL TOPIC:")
            print(f"   Title: {viral_topic['title']}")
            print(f"   Source: {viral_topic['source']}")
            print(f"   Platform: {viral_topic.get('platform', 'Unknown')}")
            if 'engagement' in viral_topic:
                print(f"   Engagement: {viral_topic['engagement']}")
            print(f"   Reason: {viral_topic.get('viral_reason', 'High viral potential')}")
            
            return True
        else:
            print("❌ No viral topic selected")
            return False
    else:
        print("❌ No articles found from any source")
        return False

if __name__ == "__main__":
    test_enhanced_news_system()


