#!/usr/bin/env python3
"""
Post with existing video file and improved, relevant caption
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption
from facebook_api import post_to_facebook_page
import os

def post_with_existing_video():
    """Post with existing video and improved caption"""
    print("="*60)
    print("POSTING WITH EXISTING VIDEO AND IMPROVED CAPTION")
    print("="*60)
    
    try:
        # Step 1: Get fresh viral news
        print("Step 1: Fetching fresh viral news...")
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
        print(f"Description: {viral_article['description'][:100]}...")
        
        # Step 3: Generate professional caption
        print("\nStep 3: Generating professional caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("Caption generation failed")
            return False
        
        print(f"Caption generated ({len(caption)} characters)")
        print(f"Preview: {caption[:200]}...")
        
        # Step 4: Use existing video file
        print("\nStep 4: Using existing video file...")
        
        # Use the most recent video file
        video_files = [
            "test_veo3_video.mp4",
            "professional_subtitle_video_20251022_162721.mp4",
            "simple_clean_subtitle_video_20251022_163226.mp4"
        ]
        
        video_file = None
        for vf in video_files:
            if os.path.exists(vf):
                video_file = vf
                break
        
        if not video_file:
            print("No video files found")
            return False
        
        print(f"Using video: {video_file}")
        print(f"Video size: {os.path.getsize(video_file)} bytes")
        
        # Step 5: Post to Facebook with video and improved caption
        print("\nStep 5: Posting to Facebook with video and improved caption...")
        success = post_to_facebook_page(caption, video_file)
        
        if success:
            print("\nSUCCESS: Video post with improved caption published!")
            print("This post now has a relevant caption that matches the news story!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = post_with_existing_video()
    
    if success:
        print("\n" + "="*60)
        print("VIDEO POST WITH IMPROVED CAPTION SUCCESSFUL!")
        print("Caption now matches the news story content")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("VIDEO POST FAILED!")
        print("="*60)


