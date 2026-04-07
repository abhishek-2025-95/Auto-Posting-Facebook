#!/usr/bin/env python3
"""
Reddit News Fetcher - Get viral breaking news from Reddit
Reddit is excellent for viral content because it's user-driven and shows what's actually trending
"""

import requests
import json
import time
from datetime import datetime, timedelta
from config import GEMINI_API_KEY
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_reddit_viral_news():
    """
    Get viral breaking news from Reddit's most popular subreddits
    Reddit is perfect for viral content because it shows what people are actually sharing
    """
    print("Fetching viral news from Reddit...")
    try:
        from config import NEWS_MARKETS_US_EUROPE_ONLY as _reddit_mkt
    except ImportError:
        _reddit_mkt = False

    if _reddit_mkt:
        # US / Europe financial markets & economy
        viral_subreddits = [
            'Economics', 'economy', 'finance', 'business', 'stocks', 'investing', 'StockMarket',
            'wallstreetbets', 'SecurityAnalysis', 'options', 'europe', 'unitedkingdom', 'ukpolitics',
            'EuropeanUnion', 'euro', 'Macroeconomics',
        ]
    else:
        # US + Europe + global breaking news (more sources = less repeats)
        viral_subreddits = [
            'worldnews', 'news', 'politics', 'USNews', 'americanpolitics',
            'technology', 'economy', 'health', 'climate',
            'europe', 'ukpolitics', 'unitedkingdom', 'germany', 'france',
            'conspiracy', 'TrueReddit', 'DepthHub', 'worldevents', 'BreakingNews',
            'business', 'science', 'space',
        ]
    
    all_posts = []
    
    for subreddit in viral_subreddits:
        try:
            # Reddit API endpoint (no auth required for public data)
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            headers = {
                'User-Agent': 'ViralNewsBot/1.0 (Educational Purpose)'
            }
            response = None
            for attempt in range(3):
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 429:
                    wait = (attempt + 1) * 5
                    print(f"Rate limited on r/{subreddit}, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                break
            if response is None or response.status_code != 200:
                continue
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts[:8]:  # Top 8 from each subreddit (more variety)
                post_data = post.get('data', {})
                
                # Extract post information
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                url_link = post_data.get('url', '')
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                created_utc = post_data.get('created_utc', 0)
                subreddit_name = post_data.get('subreddit', subreddit)
                
                # Convert timestamp
                post_date = datetime.fromtimestamp(created_utc)
                
                # Only include recent posts (last 24 hours) with good engagement
                if (datetime.now() - post_date).total_seconds() < 86400 and score > 10:
                    all_posts.append({
                        'title': title,
                        'description': selftext[:500] if selftext else title,
                        'url': url_link,
                        'source': f'Reddit r/{subreddit_name}',
                        'score': score,
                        'comments': num_comments,
                        'engagement': score + num_comments,
                        'publishedAt': post_date.isoformat(),
                        'subreddit': subreddit_name
                    })
            
            print(f"Fetched {len(posts)} posts from r/{subreddit}")

        except Exception as e:
            print(f"Error fetching from r/{subreddit}: {e}")
            continue
        # Avoid Reddit 429 rate limit: wait between subreddits
        time.sleep(1.2)
    
    # Sort by engagement (score + comments)
    all_posts.sort(key=lambda x: x['engagement'], reverse=True)
    
    # Return top 25 for more variety (fewer "all posted" skips)
    viral_posts = all_posts[:25]
    print(f"Found {len(viral_posts)} viral Reddit posts")
    
    return viral_posts


def get_reddit_bihar_news():
    """
    Fetch Bihar-related content from Reddit: search for 'Bihar' and India/Bihar subreddits.
    Used by Bihar Pulse pipeline to increase content. Returns same format as get_reddit_viral_news.
    """
    print("Fetching Bihar news from Reddit (search + India/Bihar subreddits)...")
    headers = {'User-Agent': 'BiharPulseBot/1.0 (Educational Purpose)'}
    all_posts = []
    seen_titles = set()

    def _add_post(post_data, subreddit_name, source_label=None):
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        url_link = post_data.get('url', '')
        score = post_data.get('score', 0)
        num_comments = post_data.get('num_comments', 0)
        created_utc = post_data.get('created_utc', 0)
        key = (title or '')[:80].lower()
        if key in seen_titles or not title or not url_link:
            return
        text = (title + ' ' + (selftext or '')).lower()
        if 'bihar' not in text and 'patna' not in text:
            return
        seen_titles.add(key)
        post_date = datetime.fromtimestamp(created_utc)
        all_posts.append({
            'title': title,
            'description': (selftext[:500] if selftext else title),
            'url': url_link,
            'source': source_label or f'Reddit r/{subreddit_name}',
            'score': score,
            'comments': num_comments,
            'engagement': score + num_comments,
            'publishedAt': post_date.isoformat(),
            'subreddit': subreddit_name,
        })

    # 1) Reddit search for "Bihar" across all subreddits
    try:
        r = requests.get(
            "https://www.reddit.com/search.json",
            params={'q': 'Bihar', 'sort': 'relevance', 'limit': 25, 'restrict_sr': 'false'},
            headers=headers,
            timeout=12,
        )
        r.raise_for_status()
        for child in r.json().get('data', {}).get('children', [])[:20]:
            post_data = child.get('data', {})
            sub = post_data.get('subreddit', 'search')
            _add_post(post_data, sub, f"Reddit search Bihar r/{sub}")
        print("Reddit search (Bihar): fetched.")
    except Exception as e:
        print(f"Reddit search Bihar failed: {e}")

    # 2) India / Bihar / Patna subreddits (Bihar-relevant even if title doesn't say Bihar)
    bihar_subreddits = ['india', 'IndianNews', 'IndiaSpeaks', 'bihar', 'patna']
    for subreddit in bihar_subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            posts = response.json().get('data', {}).get('children', [])
            for post in posts[:10]:
                post_data = post.get('data', {})
                _add_post(post_data, subreddit, f"Reddit r/{subreddit}")
            print(f"Fetched r/{subreddit} for Bihar pipeline.")
        except Exception as e:
            print(f"Reddit r/{subreddit}: {e}")
            continue

    all_posts.sort(key=lambda x: x['engagement'], reverse=True)
    print(f"Found {len(all_posts)} Bihar-related Reddit posts.")
    return all_posts


def select_reddit_viral_topic(posts):
    """
    Use Gemini AI to select the most viral topic from Reddit posts
    Reddit data is perfect for viral analysis because it shows real engagement
    """
    print("Analyzing Reddit posts for viral potential...")
    
    try:
        # Prepare posts for Gemini
        posts_text = ""
        for i, post in enumerate(posts, 1):
            posts_text += f"{i}. Title: {post['title']}\n"
            posts_text += f"   Subreddit: r/{post['subreddit']}\n"
            posts_text += f"   Score: {post['score']} | Comments: {post['comments']}\n"
            posts_text += f"   Engagement: {post['engagement']}\n\n"
        
        # Gemini prompt for Reddit viral analysis
        prompt = f"""
        Act as a viral trend analyst specializing in Reddit data. Given these Reddit posts with real engagement metrics, which one has the highest potential to go viral on Facebook in the US market?
        
        Reddit Posts (with engagement data):
        {posts_text}
        
        Consider:
        - Real engagement metrics (score + comments)
        - Subreddit relevance to US audience
        - Emotional impact and shareability
        - Visual potential for video content
        - Breaking news potential
        
        Return only the single best post object in this exact JSON format:
        {{
            "title": "exact title here",
            "description": "exact description here", 
            "url": "exact url here",
            "source": "exact source here",
            "subreddit": "exact subreddit here",
            "engagement": engagement_number,
            "viral_reason": "detailed explanation of why this will go viral based on Reddit engagement and content analysis"
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
        viral_post = json.loads(content)
        
        print(f"Selected viral topic: {viral_post['title']}")
        print(f"From r/{viral_post.get('subreddit', 'unknown')} with {viral_post.get('engagement', 0)} engagement")
        print(f"Viral reason: {viral_post.get('viral_reason', 'High engagement potential')}")
        
        return viral_post
        
    except Exception as e:
        print(f"Error analyzing Reddit posts with Gemini: {e}")
        # Fallback to highest engagement post
        if posts:
            print("Using fallback: selecting highest engagement post")
            return posts[0]
        else:
            print("No Reddit posts available, using emergency fallback")
            return {
                'title': 'BREAKING: Major Development Shakes Reddit Community',
                'description': 'Significant event with high engagement and viral potential',
                'url': 'https://reddit.com',
                'source': 'Reddit',
                'subreddit': 'worldnews',
                'engagement': 1000,
                'viral_reason': 'High Reddit engagement indicates viral potential'
            }

def test_reddit_news():
    """Test the Reddit news fetcher"""
    print("="*60)
    print("TESTING REDDIT VIRAL NEWS FETCHER")
    print("="*60)
    
    # Get Reddit posts
    posts = get_reddit_viral_news()
    
    if posts:
        print(f"\nFound {len(posts)} viral Reddit posts:")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post['title'][:60]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']} | Comments: {post['comments']}")
        
        # Test viral selection
        print(f"\n" + "="*40)
        print("VIRAL SELECTION:")
        print("="*40)
        
        viral_post = select_reddit_viral_topic(posts)
        print(f"\nSelected: {viral_post['title']}")
        print(f"Source: {viral_post['source']}")
        print(f"Engagement: {viral_post.get('engagement', 'N/A')}")
        print(f"Reason: {viral_post.get('viral_reason', 'No reason')}")
        
        return True
    else:
        print("No Reddit posts found")
        return False

if __name__ == "__main__":
    test_reddit_news()


