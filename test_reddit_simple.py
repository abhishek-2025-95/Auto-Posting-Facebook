#!/usr/bin/env python3
"""
Simple test of Reddit viral news system
"""

from reddit_news_fetcher import get_reddit_viral_news, select_reddit_viral_topic

def test_reddit_simple():
    print("="*60)
    print("TESTING REDDIT VIRAL NEWS SYSTEM")
    print("="*60)
    
    # Get Reddit posts
    posts = get_reddit_viral_news()
    
    if posts:
        print(f"\nFound {len(posts)} viral Reddit posts")
        
        # Show top 3 posts
        print("\nTop 3 Reddit posts:")
        for i, post in enumerate(posts[:3], 1):
            print(f"\n{i}. {post['title'][:60]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']} | Comments: {post['comments']}")
            print(f"   Engagement: {post['engagement']}")
        
        # Test viral selection
        print(f"\n" + "="*40)
        print("VIRAL SELECTION:")
        print("="*40)
        
        viral_post = select_reddit_viral_topic(posts)
        print(f"\nSelected: {viral_post['title']}")
        print(f"Source: {viral_post['source']}")
        print(f"Subreddit: r/{viral_post.get('subreddit', 'unknown')}")
        print(f"Engagement: {viral_post.get('engagement', 'N/A')}")
        print(f"Reason: {viral_post.get('viral_reason', 'No reason')}")
        
        # Check if it's truly viral content
        print(f"\n" + "="*40)
        print("VIRAL ASSESSMENT:")
        print("="*40)
        
        title = viral_post['title'].lower()
        viral_keywords = ['breaking', 'crisis', 'scandal', 'shocking', 'urgent', 'exclusive', 'ai', 'teen', 'cops', 'gun']
        found_keywords = [kw for kw in viral_keywords if kw in title]
        
        print(f"Viral keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
        print(f"Engagement score: {viral_post.get('engagement', 0)}")
        
        if viral_post.get('engagement', 0) > 5000:
            print("SUCCESS: High engagement indicates viral potential!")
        else:
            print("GOOD: Moderate engagement, still viral potential")
        
        return True
    else:
        print("No Reddit posts found")
        return False

if __name__ == "__main__":
    test_reddit_simple()


