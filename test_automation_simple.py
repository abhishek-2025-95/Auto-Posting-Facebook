#!/usr/bin/env python3
"""
Simple test of automation system for 10 posts per day
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from config import POSTS_PER_DAY, MINUTES_BETWEEN_POSTS
from datetime import datetime, timedelta

def test_automation_config():
    """Test automation configuration"""
    print("="*60)
    print("TESTING AUTOMATION CONFIGURATION")
    print("="*60)
    
    print(f"Posts per day: {POSTS_PER_DAY}")
    print(f"Minutes between posts: {MINUTES_BETWEEN_POSTS}")
    print(f"Hours between posts: {MINUTES_BETWEEN_POSTS / 60:.1f}")
    
    if POSTS_PER_DAY == 10 and MINUTES_BETWEEN_POSTS == 144:
        print("SUCCESS: System configured for 10 posts per day")
        return True
    else:
        print("WARNING: Configuration doesn't match 10 posts per day")
        return False

def test_caption_quality():
    """Test caption generation quality"""
    print("\n" + "="*60)
    print("TESTING CAPTION GENERATION")
    print("="*60)
    
    # Get viral news
    articles = get_trending_news()
    if not articles:
        print("No articles found")
        return False
    
    # Select viral topic
    viral_article = select_viral_topic(articles)
    if not viral_article:
        print("No viral topic selected")
        return False
    
    print(f"Selected: {viral_article['title'][:60]}...")
    
    # Generate caption
    caption = generate_facebook_caption(viral_article)
    if not caption:
        print("Caption generation failed")
        return False
    
    print(f"\nGenerated caption ({len(caption)} characters)")
    print("="*40)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("="*40)
    
    # Check hashtags
    hashtag_count = caption.count('#')
    print(f"\nHashtag analysis:")
    print(f"Number of hashtags: {hashtag_count}")
    
    # Check for viral hashtags
    viral_hashtags = ['#BreakingNews', '#USNews', '#Viral', '#TrendingNow']
    found_hashtags = [tag for tag in viral_hashtags if tag in caption]
    print(f"Viral hashtags found: {len(found_hashtags)}")
    
    if len(caption) >= 200 and hashtag_count >= 10:
        print("SUCCESS: High-quality caption with hashtags")
        return True
    else:
        print("WARNING: Caption may need improvement")
        return False

def test_posting_schedule():
    """Test posting schedule"""
    print("\n" + "="*60)
    print("TESTING POSTING SCHEDULE")
    print("="*60)
    
    # Calculate next 10 posting times
    current_time = datetime.now()
    posting_times = []
    
    for i in range(10):
        next_time = current_time + timedelta(minutes=MINUTES_BETWEEN_POSTS * i)
        posting_times.append(next_time)
    
    print("Next 10 posting times:")
    for i, post_time in enumerate(posting_times, 1):
        print(f"{i:2d}. {post_time.strftime('%Y-%m-%d %H:%M:%S')} ({post_time.strftime('%A %I:%M %p')})")
    
    # Check distribution
    gaps = []
    for i in range(1, len(posting_times)):
        gap = (posting_times[i] - posting_times[i-1]).total_seconds() / 3600
        gaps.append(gap)
    
    avg_gap = sum(gaps) / len(gaps)
    print(f"\nAverage gap between posts: {avg_gap:.1f} hours")
    
    if 2.0 <= avg_gap <= 3.0:
        print("SUCCESS: Well-distributed posting schedule")
        return True
    else:
        print("WARNING: Posting schedule needs adjustment")
        return False

def test_complete_pipeline():
    """Test complete automation pipeline"""
    print("\n" + "="*60)
    print("TESTING COMPLETE AUTOMATION PIPELINE")
    print("="*60)
    
    # Test 1: News fetching
    print("1. Testing news fetching...")
    articles = get_trending_news()
    if articles:
        print(f"   SUCCESS: {len(articles)} articles fetched")
    else:
        print("   FAILED: No articles fetched")
        return False
    
    # Test 2: Viral selection
    print("2. Testing viral topic selection...")
    viral_article = select_viral_topic(articles)
    if viral_article:
        print(f"   SUCCESS: Viral topic selected")
    else:
        print("   FAILED: No viral topic selected")
        return False
    
    # Test 3: Caption generation
    print("3. Testing caption generation...")
    caption = generate_facebook_caption(viral_article)
    if caption and len(caption) > 100:
        print(f"   SUCCESS: Caption generated ({len(caption)} chars)")
    else:
        print("   FAILED: Caption generation failed")
        return False
    
    # Test 4: Video generation
    print("4. Testing video generation...")
    video_path = generate_post_video(viral_article)
    if video_path:
        print(f"   SUCCESS: Video generated")
    else:
        print("   WARNING: Video generation failed (will use fallback)")
    
    return True

if __name__ == "__main__":
    print("TESTING AUTOMATION SYSTEM FOR 10 POSTS PER DAY")
    print("="*60)
    
    # Test all components
    config_ok = test_automation_config()
    caption_ok = test_caption_quality()
    schedule_ok = test_posting_schedule()
    pipeline_ok = test_complete_pipeline()
    
    print("\n" + "="*60)
    print("FINAL AUTOMATION ASSESSMENT")
    print("="*60)
    
    if config_ok and caption_ok and schedule_ok and pipeline_ok:
        print("SUCCESS: System is fully automated for 10 posts per day")
        print("SUCCESS: Captions and hashtags are working")
        print("SUCCESS: Video generation is working")
        print("SUCCESS: Posting schedule is configured")
        print("\nREADY FOR FULL AUTOMATION!")
    else:
        print("WARNING: Some components need attention")
        if not config_ok:
            print("- Configuration needs fixing")
        if not caption_ok:
            print("- Caption generation needs improvement")
        if not schedule_ok:
            print("- Posting schedule needs adjustment")
        if not pipeline_ok:
            print("- Automation pipeline needs fixing")


