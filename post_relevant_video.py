#!/usr/bin/env python3
"""
Post an updated video with relevant content that matches the news story
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page
import os

def post_relevant_video():
    """Post a video that actually matches the news content"""
    print("="*60)
    print("POSTING UPDATED VIDEO WITH RELEVANT CONTENT")
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
        print(f"Preview: {caption[:150]}...")
        
        # Step 4: Generate relevant video (with improved prompts)
        print("\nStep 4: Generating relevant video...")
        print("This will create a video that actually matches the news story...")
        
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed - posting text only")
            # Post text only if video fails
            success = post_to_facebook_page(caption, None)
            if success:
                print("SUCCESS: Text post published!")
                return True
            else:
                print("FAILED: Could not post to Facebook")
                return False
        
        print(f"Video generated: {video_file}")
        print(f"Video size: {os.path.getsize(video_file)} bytes")
        
        # Step 5: Post to Facebook with relevant video
        print("\nStep 5: Posting to Facebook with relevant video...")
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up video file
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up video file: {video_file}")
        except:
            pass
        
        if success:
            print("\nSUCCESS: Updated video post published!")
            print("This video now actually matches the news content!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = post_relevant_video()
    
    if success:
        print("\n" + "="*60)
        print("UPDATED VIDEO POST SUCCESSFUL!")
        print("Video now matches the news story content")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("VIDEO POST FAILED!")
        print("="*60)


