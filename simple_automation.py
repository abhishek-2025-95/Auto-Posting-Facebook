#!/usr/bin/env python3
"""
Simple Automation System - Basic Version
Reliable Facebook automation without complex features
"""

import time
from datetime import datetime
import os

def run_single_post():
    """Run a single automation cycle"""
    print("\n" + "="*50)
    print(f"AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        # Step 1: Get trending news
        print("\nStep 1: Fetching trending news...")
        from news_fetcher import get_trending_news, select_viral_topic
        
        article_list = get_trending_news()
        if not article_list:
            print("No articles found")
            return False
        
        print(f"Found {len(article_list)} articles")
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(article_list)
        if not viral_article:
            print("No viral article selected")
            return False
        
        print(f"Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating caption...")
        from content_generator import generate_facebook_caption
        
        caption = generate_facebook_caption(viral_article)
        if not caption:
            print("No caption generated")
            return False
        
        print("Caption generated successfully")
        
        # Step 4: Generate video
        print("\nStep 4: Generating video...")
        from content_generator import generate_post_video
        
        video_file = generate_post_video(viral_article)
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed")
            return False
        
        print("Video generated successfully")
        
        # Step 5: Post to Facebook
        print("\nStep 5: Posting to Facebook...")
        from facebook_api import post_to_facebook_page
        
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up: {video_file}")
        except:
            pass
        
        if success:
            print("\nPOST SUCCESSFUL!")
            return True
        else:
            print("\nPOST FAILED!")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("SIMPLE AUTOMATION SYSTEM")
    print("="*50)
    print("This will run a single automation cycle")
    print("="*50)
    
    # Test Facebook connection first
    print("\nTesting Facebook connection...")
    try:
        from facebook_api import test_facebook_connection
        if test_facebook_connection():
            print("Facebook connection: SUCCESS")
        else:
            print("Facebook connection: FAILED")
            return
    except Exception as e:
        print(f"Facebook connection error: {e}")
        return
    
    # Run single cycle
    print("\nRunning automation cycle...")
    success = run_single_post()
    
    if success:
        print("\n" + "="*50)
        print("AUTOMATION COMPLETE!")
        print("="*50)
        print("Your post has been made to Facebook!")
        print("Check your Facebook page to see the result.")
    else:
        print("\n" + "="*50)
        print("AUTOMATION FAILED!")
        print("="*50)
        print("Check the error messages above for details.")

if __name__ == "__main__":
    main()


