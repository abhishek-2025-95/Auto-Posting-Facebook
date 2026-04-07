#!/usr/bin/env python3
"""
Post text-only content with the improved caption
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption
from facebook_api import post_text_only

def post_text_only_content():
    """Post text-only content with improved caption"""
    print("="*60)
    print("POSTING TEXT-ONLY CONTENT WITH IMPROVED CAPTION")
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
        print(f"Preview: {caption[:200]}...")
        
        # Step 4: Post text-only to Facebook
        print("\nStep 4: Posting text-only to Facebook...")
        success = post_text_only(caption)
        
        if success:
            print("\nSUCCESS: Text-only post published!")
            print("This post has the improved, relevant caption!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = post_text_only_content()
    
    if success:
        print("\n" + "="*60)
        print("TEXT-ONLY POST SUCCESSFUL!")
        print("Post has improved, relevant caption")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("POST FAILED!")
        print("="*60)