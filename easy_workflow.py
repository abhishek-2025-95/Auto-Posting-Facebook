#!/usr/bin/env python3
"""
Easy Workflow - Simple commands for content management
"""

import os
import subprocess
import sys

def main():
    print("="*60)
    print("EASY CONTENT WORKFLOW")
    print("="*60)
    print("Choose your action:")
    print("1. Generate new content (preview only)")
    print("2. Review latest content")
    print("3. Post to Facebook")
    print("4. Exit")
    print("="*60)
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        print("\nGenerating new content...")
        subprocess.run([sys.executable, "preview_mode.py"])
        
    elif choice == '2':
        print("\nReviewing latest content...")
        # Find latest caption file
        import glob
        caption_files = glob.glob("preview_caption_*.txt")
        if caption_files:
            latest_caption = max(caption_files, key=os.path.getctime)
            print(f"\nLatest caption file: {latest_caption}")
            print("\nCaption content:")
            print("-" * 50)
            with open(latest_caption, 'r', encoding='utf-8') as f:
                print(f.read())
            print("-" * 50)
            
            # Find latest video file
            video_files = glob.glob("preview_video_*.mp4")
            if video_files:
                latest_video = max(video_files, key=os.path.getctime)
                print(f"\nLatest video file: {latest_video}")
                print(f"File size: {os.path.getsize(latest_video)} bytes")
                print(f"Location: {os.path.abspath(latest_video)}")
        else:
            print("No preview content found. Generate content first.")
            
    elif choice == '3':
        print("\nPosting to Facebook...")
        subprocess.run([sys.executable, "approve_and_post.py"])
        
    elif choice == '4':
        print("Goodbye!")
        return
        
    else:
        print("Invalid choice. Please try again.")
        main()

if __name__ == "__main__":
    main()



