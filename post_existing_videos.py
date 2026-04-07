#!/usr/bin/env python3
"""
Post all existing videos from testing sessions with their captions
"""

import os
import glob
from datetime import datetime
from facebook_api import post_to_facebook_page

def find_video_caption_pairs():
    """Find all video files and their corresponding caption files"""
    video_files = glob.glob("*.mp4")
    caption_files = glob.glob("*caption*.txt")
    
    pairs = []
    
    for video_file in video_files:
        # Find corresponding caption file
        base_name = video_file.replace('.mp4', '')
        caption_file = None
        
        # Try different naming patterns
        for caption in caption_files:
            if base_name in caption or caption.replace('_caption', '') in base_name:
                caption_file = caption
                break
        
        if caption_file and os.path.exists(caption_file):
            pairs.append((video_file, caption_file))
        else:
            print(f"WARNING: No caption found for {video_file}")
    
    return pairs

def post_existing_videos():
    """Post all existing videos with their captions"""
    print("="*60)
    print("POSTING EXISTING VIDEOS FROM TESTING SESSIONS")
    print("="*60)
    
    # Find video-caption pairs
    pairs = find_video_caption_pairs()
    
    if not pairs:
        print("No video-caption pairs found.")
        return False
    
    print(f"Found {len(pairs)} video-caption pairs:")
    for i, (video, caption) in enumerate(pairs, 1):
        print(f"{i}. {video} + {caption}")
    
    print("\n" + "="*60)
    print("STARTING POSTING PROCESS")
    print("="*60)
    
    success_count = 0
    total_count = len(pairs)
    
    for i, (video_file, caption_file) in enumerate(pairs, 1):
        print(f"\nPosting {i}/{total_count}: {video_file}")
        
        try:
            # Read caption
            with open(caption_file, 'r', encoding='utf-8') as f:
                caption = f.read()
            
            print(f"Caption length: {len(caption)} characters")
            print(f"Video size: {os.path.getsize(video_file)} bytes")
            
            # Post to Facebook
            success = post_to_facebook_page(caption, video_file)
            
            if success:
                success_count += 1
                print(f"SUCCESS: Posted {video_file}")
            else:
                print(f"FAILED: Could not post {video_file}")
            
            # Wait 30 seconds between posts to avoid rate limits
            if i < total_count:
                print("Waiting 30 seconds before next post...")
                import time
                time.sleep(30)
                
        except Exception as e:
            print(f"ERROR posting {video_file}: {e}")
    
    print("\n" + "="*60)
    print("POSTING COMPLETE")
    print("="*60)
    print(f"Successfully posted: {success_count}/{total_count} videos")
    print(f"Failed: {total_count - success_count}/{total_count} videos")
    
    if success_count > 0:
        print(f"\n{success_count} videos posted to your Facebook page!")
        print("Check your 'The Unseen Economy' page to see the posts.")
    
    return success_count > 0

if __name__ == "__main__":
    post_existing_videos()
