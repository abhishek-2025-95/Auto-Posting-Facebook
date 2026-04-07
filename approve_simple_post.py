#!/usr/bin/env python3
"""
Approve and post the simple clean subtitle video
"""

import os
import glob
from datetime import datetime
from facebook_api import post_to_facebook_page
from content_generator import generate_facebook_caption

def find_latest_simple_video():
    """Find the latest simple clean subtitle video"""
    video_files = glob.glob("simple_clean_subtitle_video_*.mp4")
    
    if not video_files:
        print("No simple clean subtitle videos found.")
        return None
    
    # Get the latest file (by timestamp in filename)
    latest_video = max(video_files, key=os.path.getctime)
    return latest_video

def approve_and_post():
    """Approve and post the simple clean subtitle video"""
    print("="*60)
    print("APPROVE AND POST SIMPLE CLEAN SUBTITLE VIDEO")
    print("="*60)
    
    # Find latest simple video
    video_file = find_latest_simple_video()
    
    if not video_file:
        print("No simple clean subtitle video found.")
        return False
    
    print(f"Found simple video: {video_file}")
    print(f"File size: {os.path.getsize(video_file)} bytes")
    print(f"Created: {datetime.fromtimestamp(os.path.getctime(video_file)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate caption for the video
    print("\nGenerating breaking news caption...")
    article = {
        'title': 'BREAKING: Major Data Breach Exposes Millions of Americans',
        'description': 'Millions of American user records have been exposed in what experts are calling the largest data breach of 2024.',
        'source': 'Breaking News Alert'
    }
    
    caption = generate_facebook_caption(article)
    if not caption:
        print("Failed to generate caption.")
        return False
    
    print(f"Caption generated ({len(caption)} characters)")
    print(f"Preview: {caption[:100]}...")
    
    # Confirm posting
    print("\n" + "="*60)
    print("READY TO POST")
    print("="*60)
    print(f"Video: {video_file}")
    print(f"Caption length: {len(caption)} characters")
    print("="*60)
    
    confirm = input("\nDo you want to post this simple clean subtitle video to Facebook? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("Posting cancelled.")
        return False
    
    # Post to Facebook
    print("\nPosting to Facebook...")
    success = post_to_facebook_page(caption, video_file)
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! SIMPLE CLEAN VIDEO POSTED!")
        print("="*60)
        print(f"Check your Facebook page for the new post")
        print(f"Video: {video_file}")
        print(f"Posted at: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        return True
    else:
        print("FAILED to post video to Facebook.")
        return False

if __name__ == "__main__":
    approve_and_post()



