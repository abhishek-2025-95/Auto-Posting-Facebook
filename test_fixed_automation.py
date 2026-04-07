#!/usr/bin/env python3
"""
Test the fixed automation system with relevant videos
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page
import os

def test_fixed_automation():
    """Test automation with fixed video generation"""
    print("="*60)
    print("TESTING FIXED AUTOMATION WITH RELEVANT VIDEOS")
    print("="*60)
    
    try:
        # Step 1: Get viral news
        print("Step 1: Fetching viral news...")
        articles = get_trending_news()
        if not articles:
            print("No articles found")
            return False
        
        print(f"Found {len(articles)} articles")
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(articles)
        if not viral_article:
            print("No viral topic selected")
            return False
        
        print(f"Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating caption...")
        caption = generate_facebook_caption(viral_article)
        if not caption:
            print("Caption generation failed")
            return False
        
        print(f"Caption generated ({len(caption)} characters)")
        
        # Step 4: Generate relevant video
        print("\nStep 4: Generating relevant video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed")
            return False
        
        print(f"Video generated: {video_file}")
        print(f"Video size: {os.path.getsize(video_file)} bytes")
        
        # Step 5: Post to Facebook
        print("\nStep 5: Posting to Facebook...")
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up video file")
        except:
            pass
        
        if success:
            print("\nSUCCESS: Post with relevant video published!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_automation()
    
    if success:
        print("\n" + "="*60)
        print("FIXED AUTOMATION SUCCESSFUL!")
        print("Videos now match the news content")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("AUTOMATION FAILED!")
        print("="*60)


