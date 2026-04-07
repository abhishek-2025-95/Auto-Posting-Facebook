#!/usr/bin/env python3
"""
Viral Content Workflow - Easy management of viral content
"""

import os
import subprocess
import sys

def main():
    print("="*60)
    print("VIRAL CONTENT WORKFLOW")
    print("="*60)
    print("Choose your action:")
    print("1. Generate new viral content (with text overlays)")
    print("2. Review latest viral content")
    print("3. Post to Facebook")
    print("4. Exit")
    print("="*60)
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        print("\nGenerating new viral content...")
        subprocess.run([sys.executable, "viral_image_generator.py"])
        
    elif choice == '2':
        print("\nReviewing latest viral content...")
        # Find latest caption file
        import glob
        caption_files = glob.glob("viral_preview_caption_*.txt")
        image_files = glob.glob("viral_image_*.jpg")
        
        if caption_files and image_files:
            latest_caption = max(caption_files, key=os.path.getctime)
            latest_image = max(image_files, key=os.path.getctime)
            
            print(f"\nLatest viral content:")
            print(f"Caption: {latest_caption}")
            print(f"Image: {latest_image}")
            
            print(f"\nCaption content:")
            print("-" * 50)
            with open(latest_caption, 'r', encoding='utf-8') as f:
                print(f.read())
            print("-" * 50)
            
            print(f"\nImage file: {latest_image}")
            print(f"File size: {os.path.getsize(latest_image)} bytes")
            print(f"Location: {os.path.abspath(latest_image)}")
        else:
            print("No viral content found. Generate content first.")
            
    elif choice == '3':
        print("\nPosting viral content to Facebook...")
        subprocess.run([sys.executable, "post_viral_content.py"])
        
    elif choice == '4':
        print("Goodbye!")
        return
        
    else:
        print("Invalid choice. Please try again.")
        main()

if __name__ == "__main__":
    main()



