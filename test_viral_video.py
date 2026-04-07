#!/usr/bin/env python3
"""
Test viral video generation with subtitles
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_post_video, generate_facebook_caption
from facebook_api import post_to_facebook_page
from datetime import datetime

def test_viral_video():
    """Test generating a viral video with subtitles"""
    print("="*60)
    print("TESTING VIRAL VIDEO WITH SUBTITLES")
    print("="*60)
    
    try:
        # Step 1: Get trending news
        print("Step 1: Fetching trending news...")
        articles = get_trending_news()
        if not articles:
            print("No articles found, using fallback content")
            articles = [{
                'title': 'Major Economic Development Shakes Global Markets',
                'description': 'Breaking news about significant economic changes affecting markets worldwide',
                'url': 'https://example.com'
            }]
        
        # Step 2: Select viral topic
        print("Step 2: Selecting most viral topic...")
        viral_article = select_viral_topic(articles)
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
        
        # Step 4: Generate viral video with subtitles
        print("Step 4: Generating viral video with subtitles...")
        video_file = generate_post_video(viral_article)
        if not video_file:
            print("Video generation failed")
            return False
        
        print(f"Viral video generated: {video_file}")
        
        # Step 5: Save preview files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preview_caption_file = f"viral_preview_caption_{timestamp}.txt"
        preview_video_file = f"viral_preview_video_{timestamp}.mp4"
        
        # Save caption to file
        with open(preview_caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)
        
        # Copy video with timestamp
        import shutil
        shutil.copy2(video_file, preview_video_file)
        
        print("\n" + "="*60)
        print("VIRAL VIDEO WITH SUBTITLES GENERATED!")
        print("="*60)
        print(f"Caption saved: {preview_caption_file}")
        print(f"Video saved: {preview_video_file}")
        print(f"Caption length: {len(caption)} characters")
        print(f"Generated at: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        print("\nREVIEW YOUR VIRAL CONTENT:")
        print("1. Check the caption file for content and hashtags")
        print("2. Watch the video to see the viral subtitles")
        print("3. If satisfied, run: python approve_and_post.py")
        print("4. If not satisfied, run: python test_viral_video.py (new content)")
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
    test_viral_video()



