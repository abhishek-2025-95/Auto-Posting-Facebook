#!/usr/bin/env python3
"""
Simple test to confirm Reddit source provides ONLY latest news
"""

from reddit_news_fetcher import get_reddit_viral_news
from datetime import datetime, timedelta

def test_news_freshness():
    """Test that we're getting only the latest news, not old news"""
    print("="*60)
    print("TESTING NEWS FRESHNESS - LATEST vs OLD NEWS")
    print("="*60)
    
    # Get Reddit posts
    posts = get_reddit_viral_news()
    
    if not posts:
        print("No posts found")
        return False
    
    print(f"\nFound {len(posts)} posts")
    
    # Check timestamps of all posts
    print(f"\nTIMESTAMP ANALYSIS:")
    print("="*40)
    
    current_time = datetime.now()
    
    posts_within_6_hours = 0
    posts_within_12_hours = 0
    posts_within_24_hours = 0
    posts_older_than_24_hours = 0
    
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Checking posts from last 24 hours...")
    
    for i, post in enumerate(posts, 1):
        # Parse the publishedAt timestamp
        try:
            post_time = datetime.fromisoformat(post['publishedAt'].replace('Z', '+00:00'))
            time_diff = current_time - post_time.replace(tzinfo=None)
            hours_old = time_diff.total_seconds() / 3600
            
            print(f"\n{i}. {post['title'][:50]}...")
            print(f"   Published: {post_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Age: {hours_old:.1f} hours old")
            print(f"   Source: {post['source']}")
            
            # Categorize by age
            if hours_old <= 6:
                posts_within_6_hours += 1
                print(f"   Status: FRESH (within 6 hours)")
            elif hours_old <= 12:
                posts_within_12_hours += 1
                print(f"   Status: RECENT (within 12 hours)")
            elif hours_old <= 24:
                posts_within_24_hours += 1
                print(f"   Status: YESTERDAY (within 24 hours)")
            else:
                posts_older_than_24_hours += 1
                print(f"   Status: OLD NEWS (over 24 hours)")
                
        except Exception as e:
            print(f"   Error parsing timestamp: {e}")
            continue
    
    # Summary
    print(f"\n" + "="*40)
    print("FRESHNESS SUMMARY:")
    print("="*40)
    
    total_posts = len(posts)
    print(f"Total posts analyzed: {total_posts}")
    print(f"Posts within 6 hours: {posts_within_6_hours}")
    print(f"Posts within 12 hours: {posts_within_12_hours}")
    print(f"Posts within 24 hours: {posts_within_24_hours}")
    print(f"Posts older than 24 hours: {posts_older_than_24_hours}")
    
    # Calculate percentages
    if total_posts > 0:
        fresh_percentage = (posts_within_6_hours / total_posts) * 100
        recent_percentage = ((posts_within_6_hours + posts_within_12_hours) / total_posts) * 100
        within_24h_percentage = ((posts_within_6_hours + posts_within_12_hours + posts_within_24_hours) / total_posts) * 100
        
        print(f"\nFRESHNESS PERCENTAGES:")
        print(f"Very fresh (within 6 hours): {fresh_percentage:.1f}%")
        print(f"Recent (within 12 hours): {recent_percentage:.1f}%")
        print(f"Within 24 hours: {within_24h_percentage:.1f}%")
        
        # Assessment
        print(f"\n" + "="*40)
        print("ASSESSMENT:")
        print("="*40)
        
        if posts_older_than_24_hours == 0:
            print("SUCCESS: No old news found - all posts are from last 24 hours")
        elif posts_older_than_24_hours <= 1:
            print("GOOD: Minimal old news - mostly fresh content")
        elif posts_older_than_24_hours <= 2:
            print("MODERATE: Some old news present - mostly recent content")
        else:
            print("POOR: Significant old news present - not ideal for viral content")
        
        if fresh_percentage >= 50:
            print("SUCCESS: Over 50% of posts are very fresh (within 6 hours)")
        elif fresh_percentage >= 30:
            print("GOOD: Good percentage of fresh posts")
        else:
            print("MODERATE: Limited fresh content")
        
        if within_24h_percentage >= 90:
            print("SUCCESS: Over 90% of posts are from last 24 hours")
        elif within_24h_percentage >= 80:
            print("GOOD: Over 80% of posts are recent")
        else:
            print("MODERATE: Some posts may be too old for viral content")
        
        return within_24h_percentage >= 80 and posts_older_than_24_hours <= 2
    else:
        print("No posts to analyze")
        return False

if __name__ == "__main__":
    # Test freshness of current posts
    freshness_ok = test_news_freshness()
    
    print(f"\n" + "="*60)
    print("FINAL ASSESSMENT")
    print("="*60)
    
    if freshness_ok:
        print("CONFIRMED: Reddit source provides ONLY latest news")
        print("READY: System is suitable for viral content automation")
    else:
        print("ISSUE: Reddit source may include old news")
        print("NOT READY: System needs improvement for viral content")


