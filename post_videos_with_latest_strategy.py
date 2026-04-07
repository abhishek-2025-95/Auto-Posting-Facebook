#!/usr/bin/env python3
"""
Post existing videos with fresh captions using our latest breaking news strategy
"""

import os
import glob
from datetime import datetime
from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption
from facebook_api import post_to_facebook_page

def post_videos_with_latest_strategy():
    """Post existing videos with fresh breaking news captions"""
    print("="*60)
    print("POSTING VIDEOS WITH LATEST BREAKING NEWS STRATEGY")
    print("="*60)
    
    # Find all video files
    video_files = glob.glob("*.mp4")
    
    if not video_files:
        print("No video files found.")
        return False
    
    print(f"Found {len(video_files)} video files:")
    for i, video in enumerate(video_files, 1):
        print(f"{i}. {video}")
    
    print("\n" + "="*60)
    print("GENERATING FRESH BREAKING NEWS CONTENT")
    print("="*60)
    
    # Get fresh breaking news for each video
    success_count = 0
    total_count = len(video_files)
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\nProcessing {i}/{total_count}: {video_file}")
        
        try:
            # Step 1: Get fresh breaking news
            print("Fetching fresh US breaking news...")
            article_list = get_trending_news()
            
            if not article_list:
                print("No articles fetched. Using fallback content.")
                # Use fallback breaking news
                viral_article = {
                    'title': 'BREAKING: Major US Development Shakes Nation',
                    'description': 'Significant event with far-reaching implications for the United States.',
                    'source': 'Breaking News Alert'
                }
            else:
                # Select viral topic
                print("Selecting most viral topic...")
                viral_article = select_viral_topic(article_list)
            
            print(f"Selected topic: {viral_article['title']}")
            
            # Step 2: Generate fresh caption with latest strategy
            print("Generating breaking news caption...")
            caption = generate_facebook_caption(viral_article)
            
            if not caption:
                print("Caption generation failed. Skipping this video.")
                continue
            
            print(f"Caption generated ({len(caption)} characters)")
            print(f"Preview: {caption[:100]}...")
            
            # Step 3: Post to Facebook
            print("Posting to Facebook...")
            success = post_to_facebook_page(caption, video_file)
            
            if success:
                success_count += 1
                print(f"SUCCESS: Posted {video_file}")
            else:
                print(f"FAILED: Could not post {video_file}")
            
            # Wait 2 minutes between posts to avoid rate limits
            if i < total_count:
                print("Waiting 2 minutes before next post...")
                import time
                time.sleep(120)
                
        except Exception as e:
            print(f"ERROR processing {video_file}: {e}")
    
    print("\n" + "="*60)
    print("POSTING COMPLETE")
    print("="*60)
    print(f"Successfully posted: {success_count}/{total_count} videos")
    print(f"Failed: {total_count - success_count}/{total_count} videos")
    
    if success_count > 0:
        print(f"\n{success_count} videos posted with fresh breaking news content!")
        print("Check your 'The Unseen Economy' page to see the posts.")
    
    return success_count > 0

if __name__ == "__main__":
    post_videos_with_latest_strategy()



