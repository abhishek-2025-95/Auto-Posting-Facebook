#!/usr/bin/env python3
"""
Google News Fetcher - Scrape Google News for viral breaking news
Google News aggregates from major sources and shows trending topics
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from config import GEMINI_API_KEY
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_google_news_viral():
    """
    Scrape Google News for viral breaking news
    Google News is great because it aggregates from major sources and shows trending topics
    """
    print("Fetching viral news from Google News...")
    try:
        from config import NEWS_MARKETS_US_EUROPE_ONLY as _gn_mkt
    except ImportError:
        _gn_mkt = False

    try:
        if _gn_mkt:
            # Business / markets–heavy SERP (US edition); still scraped like top stories
            url = (
                "https://news.google.com/search?q=stock+market+US+Europe+economy+business"
                "&hl=en-US&gl=US&ceid=US%3Aen"
            )
        else:
            url = "https://news.google.com/topstories?hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        
        # Find article links in Google News
        article_links = soup.find_all('a', href=True)
        
        for link in article_links[:50]:  # Check first 50 links
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filter for actual news articles (not navigation)
            if (href.startswith('./articles/') or 'news' in href.lower()) and len(text) > 20:
                # Clean up the text
                if text and not text.startswith('Google'):
                    articles.append({
                        'title': text,
                        'url': f"https://news.google.com{href}" if href.startswith('./') else href,
                        'source': 'Google News',
                        'publishedAt': datetime.now().isoformat()
                    })
        
        # Remove duplicates and limit
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            if article['title'] not in seen_titles:
                unique_articles.append(article)
                seen_titles.add(article['title'])
        
        print(f"Found {len(unique_articles)} Google News articles")
        return unique_articles[:10]  # Top 10
        
    except Exception as e:
        print(f"Error fetching Google News: {e}")
        return []

def get_trending_google_topics():
    """
    Get trending topics from Google News
    """
    print("Fetching trending topics from Google News...")
    
    try:
        # Google News trending topics
        url = "https://news.google.com/trending?hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        trending_topics = []
        
        # Find trending topic links
        topic_links = soup.find_all('a', href=True)
        
        for link in topic_links[:20]:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if text and len(text) > 5 and 'trending' in href.lower():
                trending_topics.append({
                    'topic': text,
                    'url': f"https://news.google.com{href}" if href.startswith('./') else href,
                    'source': 'Google Trends'
                })
        
        print(f"Found {len(trending_topics)} trending topics")
        return trending_topics
        
    except Exception as e:
        print(f"Error fetching trending topics: {e}")
        return []

def select_google_viral_topic(articles):
    """
    Use Gemini AI to select the most viral topic from Google News
    """
    print("Analyzing Google News for viral potential...")
    
    try:
        # Prepare articles for Gemini
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"{i}. Title: {article['title']}\n"
            articles_text += f"   Source: {article['source']}\n\n"
        
        # Gemini prompt for Google News viral analysis
        prompt = f"""
        Act as a viral trend analyst specializing in Google News data. Given these Google News headlines, which one has the highest potential to go viral on Facebook in the US market?
        
        Google News Articles:
        {articles_text}
        
        Consider:
        - Breaking news potential
        - Emotional impact and shareability
        - Visual potential for video content
        - Relevance to US audience
        - Trending topic potential
        
        Return only the single best article object in this exact JSON format:
        {{
            "title": "exact title here",
            "description": "exact title here (use as description)", 
            "url": "exact url here",
            "source": "exact source here",
            "viral_reason": "detailed explanation of why this will go viral based on Google News trending data"
        }}
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        viral_article = json.loads(content)
        
        print(f"Selected viral topic: {viral_article['title']}")
        print(f"Viral reason: {viral_article.get('viral_reason', 'High trending potential')}")
        
        return viral_article
        
    except Exception as e:
        print(f"Error analyzing Google News with Gemini: {e}")
        # Fallback to first article
        if articles:
            print("Using fallback: selecting first article")
            return articles[0]
        else:
            print("No Google News articles available, using emergency fallback")
            return {
                'title': 'BREAKING: Major Development from Google News',
                'description': 'Significant event trending on Google News',
                'url': 'https://news.google.com',
                'source': 'Google News',
                'viral_reason': 'High trending potential on Google News'
            }

def test_google_news():
    """Test the Google News fetcher"""
    print("="*60)
    print("TESTING GOOGLE NEWS VIRAL FETCHER")
    print("="*60)
    
    # Get Google News articles
    articles = get_google_news_viral()
    
    if articles:
        print(f"\nFound {len(articles)} Google News articles:")
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. {article['title'][:60]}...")
        
        # Test viral selection
        print(f"\n" + "="*40)
        print("VIRAL SELECTION:")
        print("="*40)
        
        viral_article = select_google_viral_topic(articles)
        print(f"\nSelected: {viral_article['title']}")
        print(f"Source: {viral_article['source']}")
        print(f"Reason: {viral_article.get('viral_reason', 'No reason')}")
        
        return True
    else:
        print("No Google News articles found")
        return False

if __name__ == "__main__":
    test_google_news()


