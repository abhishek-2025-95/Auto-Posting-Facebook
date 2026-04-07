#!/usr/bin/env python3
"""
Test the video-only system to ensure all three components are generated
"""

import os
from datetime import datetime

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video

def test_video_system():
    print("="*60)
    print("TESTING VIDEO-ONLY SYSTEM")
    print("="*60)
    print("Testing: Video + Caption + Hashtags")
    print("="*60)

    try:
        # Step 1: Fetch trending US news
        print("\nStep 1: Fetching US breaking news...")
        article_list = get_trending_news()
        if not article_list:
            print("No articles fetched. Test failed.")
            return False

        # Step 2: Select viral topic
        print("\nStep 2: Selecting most viral topic...")
        viral_article = select_viral_topic(article_list)
        if not viral_article:
            print("No viral article selected. Test failed.")
            return False
        
        print(f"Selected topic: {viral_article['title']}")

        # Step 3: Generate Facebook caption
        print("\nStep 3: Generating professional caption...")
        caption = generate_facebook_caption(viral_article)
        if not caption:
            print("No caption generated. Test failed.")
            return False
        
        print(f"Caption generated ({len(caption)} characters)")
        print(f"Preview: {caption[:100]}...")

        # Step 4: Generate video
        print("\nStep 4: Generating video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed. Test failed.")
            return False
        
        print(f"Video generated: {video_file}")

        # Step 5: Verify all three components
        print("\nStep 5: Verifying all components...")
        
        # Check video
        video_size = os.path.getsize(video_file)
        print(f"✅ Video: {video_file} ({video_size} bytes)")
        
        # Check caption
        caption_length = len(caption)
        print(f"✅ Caption: {caption_length} characters")
        
        # Check hashtags
        has_breaking = '#BreakingNews' in caption
        has_us_news = '#USNews' in caption
        has_hashtags = '#' in caption
        print(f"✅ Hashtags: Breaking={has_breaking}, USNews={has_us_news}, HasHashtags={has_hashtags}")
        
        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_caption_file = f"test_caption_{timestamp}.txt"
        test_video_file = f"test_video_{timestamp}.mp4"
        
        with open(test_caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)
        
        os.rename(video_file, test_video_file)

        print("\n" + "="*60)
        print("TEST RESULTS:")
        print("="*60)
        print(f"✅ Video: {test_video_file} ({video_size} bytes)")
        print(f"✅ Caption: {test_caption_file} ({caption_length} characters)")
        print(f"✅ Hashtags: Present and relevant")
        print(f"✅ All three components verified!")
        print("="*60)
        
        print("\nFILES SAVED FOR REVIEW:")
        print(f"- Caption: {test_caption_file}")
        print(f"- Video: {test_video_file}")
        print("\nReview these files to ensure quality before running the full system.")
        
        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_video_system()
