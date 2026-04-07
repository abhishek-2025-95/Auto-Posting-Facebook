#!/usr/bin/env python3
"""
Viral Image Generator - Create engaging images with viral text overlays
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_image_fallback
from simple_subtitle_enhancer import create_viral_image_with_text
from facebook_api import post_to_facebook_page
from datetime import datetime

def create_viral_content():
    """Create viral content with text overlays"""
    print("="*60)
    print("CREATING VIRAL CONTENT WITH TEXT OVERLAYS")
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
        
        # Step 4: Generate base image
        print("Step 4: Generating base image...")
        base_image = generate_post_image_fallback(viral_article)
        if not base_image:
            print("Image generation failed")
            return None
        
        # Step 5: Add viral text overlays
        print("Step 5: Adding viral text overlays...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        viral_image = f"viral_image_{timestamp}.jpg"
        
        enhanced_image = create_viral_image_with_text(base_image, caption, viral_image)
        
        if not enhanced_image:
            print("Failed to add text overlays, using base image")
            enhanced_image = base_image
        
        # Step 6: Save preview files
        preview_caption_file = f"viral_preview_caption_{timestamp}.txt"
        
        # Save caption to file
        with open(preview_caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)
        
        print("\n" + "="*60)
        print("VIRAL CONTENT WITH TEXT OVERLAYS GENERATED!")
        print("="*60)
        print(f"Caption saved: {preview_caption_file}")
        print(f"Image saved: {enhanced_image}")
        print(f"Caption length: {len(caption)} characters")
        print(f"Generated at: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        print("\nREVIEW YOUR VIRAL CONTENT:")
        print("1. Check the caption file for content and hashtags")
        print("2. View the image to see the viral text overlays")
        print("3. If satisfied, run: python post_viral_content.py")
        print("4. If not satisfied, run: python viral_image_generator.py (new content)")
        print("="*60)
        
        return {
            'caption_file': preview_caption_file,
            'image_file': enhanced_image,
            'caption': caption,
            'article': viral_article
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    create_viral_content()



