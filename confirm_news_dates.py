#!/usr/bin/env python3
"""
Confirm the exact dates of news being provided by the system
"""

from reddit_news_fetcher import get_reddit_viral_news
from datetime import datetime, timedelta

def confirm_news_dates():
    """Confirm the exact dates of all news articles"""
    print("="*60)
    print("CONFIRMING EXACT DATES OF NEWS ARTICLES")
    print("="*60)
    
    # Get current date and time
    current_time = datetime.now()
    print(f"Current Date & Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Today's Date: {current_time.strftime('%Y-%m-%d')}")
    print(f"Current Day: {current_time.strftime('%A')}")
    
    # Get Reddit posts
    posts = get_reddit_viral_news()
    
    if not posts:
        print("\nNo posts found")
        return False
    
    print(f"\nFound {len(posts)} news articles")
    print("="*60)
    
    # Analyze each post's date
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. ARTICLE: {post['title'][:60]}...")
        print(f"   Source: {post['source']}")
        
        try:
            # Parse the publishedAt timestamp
            post_time = datetime.fromisoformat(post['publishedAt'].replace('Z', '+00:00'))
            
            # Calculate time difference
            time_diff = current_time - post_time.replace(tzinfo=None)
            hours_old = time_diff.total_seconds() / 3600
            days_old = hours_old / 24
            
            print(f"   Published Date: {post_time.strftime('%Y-%m-%d')}")
            print(f"   Published Time: {post_time.strftime('%H:%M:%S')}")
            print(f"   Published Day: {post_time.strftime('%A')}")
            print(f"   Age: {hours_old:.1f} hours old ({days_old:.1f} days old)")
            
            # Determine if it's today, yesterday, or older
            if post_time.date() == current_time.date():
                print(f"   Status: TODAY'S NEWS")
            elif post_time.date() == (current_time - timedelta(days=1)).date():
                print(f"   Status: YESTERDAY'S NEWS")
            elif post_time.date() == (current_time - timedelta(days=2)).date():
                print(f"   Status: 2 DAYS OLD")
            elif post_time.date() == (current_time - timedelta(days=3)).date():
                print(f"   Status: 3 DAYS OLD")
            else:
                print(f"   Status: OLDER THAN 3 DAYS")
                
        except Exception as e:
            print(f"   Error parsing date: {e}")
            continue
    
    # Summary by date
    print(f"\n" + "="*60)
    print("DATE SUMMARY:")
    print("="*60)
    
    today_count = 0
    yesterday_count = 0
    older_count = 0
    
    for post in posts:
        try:
            post_time = datetime.fromisoformat(post['publishedAt'].replace('Z', '+00:00'))
            if post_time.date() == current_time.date():
                today_count += 1
            elif post_time.date() == (current_time - timedelta(days=1)).date():
                yesterday_count += 1
            else:
                older_count += 1
        except:
            continue
    
    print(f"Today's news: {today_count} articles")
    print(f"Yesterday's news: {yesterday_count} articles")
    print(f"Older news: {older_count} articles")
    
    # Show specific dates found
    print(f"\nDATES FOUND:")
    unique_dates = set()
    for post in posts:
        try:
            post_time = datetime.fromisoformat(post['publishedAt'].replace('Z', '+00:00'))
            unique_dates.add(post_time.strftime('%Y-%m-%d'))
        except:
            continue
    
    for date in sorted(unique_dates):
        print(f"  - {date}")
    
    # Final confirmation
    print(f"\n" + "="*60)
    print("FINAL DATE CONFIRMATION:")
    print("="*60)
    
    if older_count == 0:
        print("CONFIRMED: All news is from today or yesterday")
        print("CONFIRMED: No old news (older than 2 days) found")
    elif older_count <= 1:
        print("CONFIRMED: Mostly fresh news with minimal old content")
    else:
        print("WARNING: Some old news detected")
    
    if today_count > 0:
        print(f"CONFIRMED: {today_count} articles are from TODAY")
    
    return older_count == 0

if __name__ == "__main__":
    confirm_news_dates()


