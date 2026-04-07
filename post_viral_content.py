#!/usr/bin/env python3
"""
Post Viral Content - Post the latest viral content to Facebook
"""

import glob
import os
from facebook_api import post_to_facebook_page
from datetime import datetime

def find_latest_viral_content():
    """Find the latest viral content files"""
    caption_files = glob.glob("viral_preview_caption_*.txt")
    image_files = glob.glob("viral_image_*.jpg")
    
    if not caption_files or not image_files:
        print("No viral content found. Run viral_image_generator.py first.")
        return None, None
    
    # Get the latest files (by timestamp in filename)
    latest_caption = max(caption_files, key=os.path.getctime)
    latest_image = max(image_files, key=os.path.getctime)
    
    return latest_caption, latest_image

def post_viral_content():
    """Post the latest viral content to Facebook"""
    print("="*60)
    print("POSTING VIRAL CONTENT TO FACEBOOK")
    print("="*60)
    
    # Find latest viral content files
    caption_file, image_file = find_latest_viral_content()
    
    if not caption_file or not image_file:
        print("No viral content found. Generate content first.")
        return False
    
    print(f"Found viral content files:")
    print(f"Caption: {caption_file}")
    print(f"Image: {image_file}")
    
    # Read caption
    with open(caption_file, 'r', encoding='utf-8') as f:
        caption = f.read()
    
    print(f"\nCaption preview ({len(caption)} characters):")
    print("-" * 40)
    print(caption[:200] + "..." if len(caption) > 200 else caption)
    print("-" * 40)
    
    # Confirm posting
    print(f"\nImage file: {image_file}")
    print(f"File size: {os.path.getsize(image_file)} bytes")
    
    confirm = input("\nDo you want to post this viral content to Facebook? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("Posting cancelled.")
        return False
    
    # Post to Facebook
    print("\nPosting to Facebook...")
    success = post_to_facebook_page(caption, image_file)
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! VIRAL CONTENT POSTED TO FACEBOOK!")
        print("="*60)
        print(f"Check your Facebook page for the new post")
        print(f"Image: {image_file}")
        print(f"Caption: {caption_file}")
        print(f"Posted at: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # Optionally clean up preview files
        cleanup = input("\nClean up preview files? (y/n): ").lower().strip()
        if cleanup == 'y':
            try:
                os.remove(caption_file)
                print("Preview files cleaned up.")
            except:
                print("Could not clean up preview files.")
        
        return True
    else:
        print("Failed to post to Facebook.")
        return False

if __name__ == "__main__":
    post_viral_content()



