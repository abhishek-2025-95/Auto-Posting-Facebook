#!/usr/bin/env python3
"""
Content Workflow - Easy management of preview and posting
"""

import os
import glob
from datetime import datetime

def show_menu():
    """Show the main menu"""
    print("="*60)
    print("VIRAL CONTENT WORKFLOW")
    print("="*60)
    print("1. Generate new preview content")
    print("2. Review existing preview content")
    print("3. Approve and post to Facebook")
    print("4. List all preview files")
    print("5. Clean up preview files")
    print("6. Exit")
    print("="*60)

def list_preview_files():
    """List all preview files"""
    caption_files = glob.glob("preview_caption_*.txt")
    video_files = glob.glob("preview_video_*.mp4")
    
    print("\nPREVIEW FILES:")
    print("-" * 40)
    
    if caption_files:
        print("Caption files:")
        for file in sorted(caption_files, key=os.path.getctime, reverse=True):
            size = os.path.getsize(file)
            time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%H:%M:%S')
            print(f"  📝 {file} ({size} bytes) - {time}")
    else:
        print("No caption files found")
    
    if video_files:
        print("\nVideo files:")
        for file in sorted(video_files, key=os.path.getctime, reverse=True):
            size = os.path.getsize(file)
            time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%H:%M:%S')
            print(f"  🎬 {file} ({size} bytes) - {time}")
    else:
        print("No video files found")

def review_content():
    """Review the latest preview content"""
    caption_files = glob.glob("preview_caption_*.txt")
    video_files = glob.glob("preview_video_*.mp4")
    
    if not caption_files or not video_files:
        print("No preview files found. Generate content first.")
        return
    
    # Get the latest files
    latest_caption = max(caption_files, key=os.path.getctime)
    latest_video = max(video_files, key=os.path.getctime)
    
    print(f"\nREVIEWING LATEST CONTENT:")
    print(f"📝 Caption: {latest_caption}")
    print(f"🎬 Video: {latest_video}")
    
    # Show caption content
    with open(latest_caption, 'r', encoding='utf-8') as f:
        caption = f.read()
    
    print(f"\nCaption content ({len(caption)} characters):")
    print("-" * 50)
    print(caption)
    print("-" * 50)
    
    print(f"\nVideo file: {latest_video}")
    print(f"File size: {os.path.getsize(latest_video)} bytes")
    print(f"Created: {datetime.fromtimestamp(os.path.getctime(latest_video)).strftime('%Y-%m-%d %H:%M:%S')}")

def clean_up_files():
    """Clean up preview files"""
    caption_files = glob.glob("preview_caption_*.txt")
    video_files = glob.glob("preview_video_*.mp4")
    
    if not caption_files and not video_files:
        print("No preview files to clean up.")
        return
    
    print(f"Found {len(caption_files)} caption files and {len(video_files)} video files.")
    confirm = input("Delete all preview files? (y/n): ").lower().strip()
    
    if confirm == 'y':
        deleted = 0
        for file in caption_files + video_files:
            try:
                os.remove(file)
                deleted += 1
            except:
                print(f"Could not delete {file}")
        print(f"Deleted {deleted} files.")
    else:
        print("Cleanup cancelled.")

def main():
    """Main workflow loop"""
    while True:
        show_menu()
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            print("\nGenerating new preview content...")
            os.system("python preview_mode.py")
        elif choice == '2':
            review_content()
        elif choice == '3':
            print("\nApproving and posting...")
            os.system("python approve_and_post.py")
        elif choice == '4':
            list_preview_files()
        elif choice == '5':
            clean_up_files()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()



