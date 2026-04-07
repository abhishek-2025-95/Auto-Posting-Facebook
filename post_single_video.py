#!/usr/bin/env python3
"""
Post a single video with full captions and hashtags
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page
from datetime import datetime

def post_single_video():
    """Post one video with full captions and hashtags"""
    print("="*60)
    print("POSTING SINGLE VIRAL VIDEO")
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
        print(f"Preview: {caption[:100]}...")
        
        # Step 4: Generate 8-second video
        print("Step 4: Generating 8-second professional video...")
        video_file = generate_post_video(viral_article)
        if not video_file:
            print("Video generation failed. Veo 3 only mode — aborting.")
            return
        
        print(f"Video generated: {video_file}")
        
        # Step 5: Post to Facebook
        print("Step 5: Posting to Facebook...")
        success = post_to_facebook_page(caption, video_file)
        
        if success:
            print("\n" + "="*60)
            print("🎉 SUCCESS! VIDEO POSTED TO FACEBOOK!")
            print("="*60)
            print(f"📱 Check your Facebook page for the new post")
            print(f"🎬 Video: {video_file}")
            print(f"📝 Caption length: {len(caption)} characters")
            print(f"⏰ Posted at: {datetime.now().strftime('%H:%M:%S')}")
            print("="*60)
        else:
            print("❌ Failed to post to Facebook")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    post_single_video()
