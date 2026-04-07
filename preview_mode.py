#!/usr/bin/env python3
"""
Preview Mode - Generate content but don't post until approved
"""

from trends_fetcher import get_us_trending_topics, select_top_trend
from content_generator import generate_facebook_caption, generate_post_video
from datetime import datetime
import os

def preview_content():
    """Generate content for preview without posting"""
    print("="*60)
    print("PREVIEW MODE - GENERATING CONTENT")
    print("="*60)
    print("This will create content but NOT post to Facebook")
    print("Review everything before approving")
    print("="*60)
    
    try:
        # Step 1: Get US Google Trends topics
        print("Step 1: Fetching US Google Trends...")
        articles = get_us_trending_topics()
        if not articles:
            print("No articles found, using fallback content")
            articles = [{
                'title': 'Major Economic Development Shakes Global Markets',
                'description': 'Breaking news about significant economic changes affecting markets worldwide',
                'url': 'https://example.com'
            }]
        
        # Step 2: Select viral topic
        print("Step 2: Selecting most viral topic...")
        viral_article = select_top_trend(articles)
        if not viral_article:
            viral_article = articles[0]
        
        print(f"Selected topic: {viral_article['title']}")
        
        # Step 3: Generate professional caption
        print("Step 3: Generating professional caption...")
        caption = generate_facebook_caption(viral_article)
        if not caption:
            caption = f"""
🚨 BREAKING: {viral_article['title']}

This development has significant implications for markets and policy makers. Stay informed as this story develops.

#BreakingNews #WorldNews #USNews #EUNews #CurrentEvents #News #Update #Alert #Trending #Viral #Important #Analysis #Insight #Policy #Economy #Politics
"""
        
        print(f"Caption generated ({len(caption)} characters)")
        
        # Step 4: Generate 8-second video
        print("Step 4: Generating 8-second professional video...")
        video_file = generate_post_video(viral_article)
        if not video_file:
            print("Video generation failed. Veo 3 only mode — no fallback will be used.")
            return None
        
        print(f"Video generated: {video_file}")
        
        # Step 5: Save preview files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preview_caption_file = f"preview_caption_{timestamp}.txt"
        preview_video_file = f"preview_video_{timestamp}.mp4"
        
        # Save caption to file
        with open(preview_caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)
        
        # Copy video with timestamp
        import shutil
        shutil.copy2(video_file, preview_video_file)
        
        print("\n" + "="*60)
        print("PREVIEW CONTENT GENERATED!")
        print("="*60)
        print(f"📝 Caption saved: {preview_caption_file}")
        print(f"🎬 Video saved: {preview_video_file}")
        print(f"📊 Caption length: {len(caption)} characters")
        print(f"⏰ Generated at: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        print("\nREVIEW YOUR CONTENT:")
        print("1. Check the caption file for content and hashtags")
        print("2. Watch the video to ensure quality")
        print("3. If satisfied, run: python approve_and_post.py")
        print("4. If not satisfied, run: python preview_mode.py (new content)")
        print("="*60)
        
        return {
            'caption_file': preview_caption_file,
            'video_file': preview_video_file,
            'caption': caption,
            'article': viral_article
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    preview_content()
