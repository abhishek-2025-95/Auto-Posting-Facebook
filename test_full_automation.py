#!/usr/bin/env python3
"""
Test full automation cycle without Unicode issues
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page
import os

def test_full_automation_cycle():
    """Test a complete automation cycle"""
    print("="*60)
    print("TESTING FULL AUTOMATION CYCLE")
    print("="*60)
    
    try:
        # Step 1: Get trending news
        print("\nStep 1: Fetching trending news...")
        articles = get_trending_news()
        
        if not articles:
            print("No articles found, skipping cycle")
            return False
        
        print(f"Found {len(articles)} articles")
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(articles)
        
        if not viral_article:
            print("No viral article selected, skipping cycle")
            return False
        
        print(f"Selected: {viral_article['title'][:60]}...")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating Facebook caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("No caption generated, skipping cycle")
            return False
        
        print(f"Caption generated ({len(caption)} characters)")
        print(f"Preview: {caption[:100]}...")
        
        # Step 4: Generate video
        print("\nStep 4: Generating post video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed, using text-only post")
            # Post text only
            success = post_to_facebook_page(caption, None)
        else:
            print(f"Video generated: {video_file}")
            # Post with video
            success = post_to_facebook_page(caption, video_file)
            
            # Clean up video file
            try:
                if os.path.exists(video_file):
                    os.remove(video_file)
                    print(f"Cleaned up video file: {video_file}")
            except:
                pass
        
        if success:
            print("\nSUCCESS: Post published to Facebook!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR in automation cycle: {e}")
        return False

if __name__ == "__main__":
    success = test_full_automation_cycle()
    
    if success:
        print("\n" + "="*60)
        print("AUTOMATION CYCLE SUCCESSFUL!")
        print("System is ready for 10 posts per day")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("AUTOMATION CYCLE FAILED!")
        print("Check the errors above")
        print("="*60)


