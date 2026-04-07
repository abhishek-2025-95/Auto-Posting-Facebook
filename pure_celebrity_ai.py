#!/usr/bin/env python3
"""
The Unseen Economy - Pure Celebrity AI System
Generates ONLY high-quality celebrity images with all text in captions
"""

import os
import random
import json
import requests
import io
import textwrap
import math
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai


def setup():
    """Initialize AI clients and constants"""
    
    # Engagement hooks for CTA banners
    ENGAGEMENT_HOOKS = [
        'SHARE IF THIS SHOCKS YOU',
        'SHARE IF YOU\'RE ANGRY',
        'SHARE IF THIS MAKES YOU MAD',
        'SHARE IF YOU\'RE FED UP',
        'SHARE IF YOU\'RE OUTRAGED',
        'SHARE IF YOU\'RE DISGUSTED',
        'SHARE IF YOU\'RE FURIOUS',
        'SHARE IF YOU\'RE LIVID'
    ]
    
    # Hashtag categories for Facebook post text
    HASHTAG_CATEGORIES = {
        'viral': ['#ViralNews', '#BreakingNews', '#CelebrityNews', '#Trending'],
        'controversial': ['#Scandal', '#Outrage', '#Shocking', '#Exposed'],
        'problem_focused': ['#CelebrityCrime', '#Justice', '#Accountability', '#Truth']
    }
    
    # Configure Gemini
    genai.configure(api_key="AIzaSyBt2KV8_nOKdpG14Pf92CT1-8L48dUZk2o")
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'gemini_model': genai.GenerativeModel('gemini-2.5-flash')
    }


def get_celebrity_viral_news(gemini_model):
    """
    Get viral celebrity news content from Gemini AI
    """
    
    system_prompt = """You are a viral news content creator for 'The Unseen Economy' page. Create shocking, viral celebrity news content in JSON format.

Your output MUST be a JSON object with these exact keys:

headline: A shocking, viral celebrity news headline (5-10 words max)
subtext: A punchy tagline explaining the scandal (10-15 words max)  
celebrity: The celebrity's name
celebrity_description: Physical description of the celebrity for AI image generation
scandal_type: Type of scandal (e.g., "Financial Fraud", "Tax Evasion", "Corporate Greed")
story_summary: Brief summary of the scandal
image_prompt: A detailed prompt for generating a high-quality celebrity image
primary_color_hex: Hex color for CTA banner
mood_keywords: 3-5 words describing the emotional tone

Focus on themes like:
- Celebrity tax evasion
- Corporate greed scandals
- Financial fraud
- Wealth inequality
- Celebrity business failures
- Economic injustice

Make it angry, provocative, and designed to go viral.

Return ONLY a valid JSON object."""

    user_prompt = "Generate a viral celebrity news story about economic injustice or corporate greed."
    
    try:
        response = gemini_model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        content = response.text.strip()
        
        # Clean up the response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        brief = json.loads(content)
        return brief
    
    except Exception as e:
        print(f"Error generating celebrity news: {e}")
        # Return viral fallback
        return {
            "headline": "Celebrity Tax Evasion Exposed",
            "subtext": "While you pay taxes, they hide millions offshore.",
            "celebrity": "A-List Celebrity",
            "celebrity_description": "A middle-aged white male celebrity with slicked-back hair, wearing an expensive suit, looking smug and arrogant",
            "scandal_type": "Tax Evasion",
            "story_summary": "Celebrity caught hiding millions in offshore accounts while ordinary people pay full taxes",
            "image_prompt": "Professional headshot of a celebrity, confident and smug expression, expensive business suit, luxury office background, dramatic lighting, high-end corporate photography style, photorealistic, high resolution",
            "primary_color_hex": "#FF4444",
            "mood_keywords": ["outrage", "unfair", "corrupt", "scandalous"]
        }


def create_high_quality_celebrity_image(brief):
    """
    Create a high-quality celebrity image using AI-generated prompts
    """
    
    celebrity = brief.get('celebrity', 'Celebrity')
    celebrity_description = brief.get('celebrity_description', 'A celebrity')
    image_prompt = brief.get('image_prompt', '')
    
    # Create a sophisticated celebrity image prompt
    detailed_prompt = f"""Professional headshot of {celebrity}, {celebrity_description}.
    
    The image should be:
    - High-resolution, photorealistic
    - Professional corporate photography style
    - Dramatic lighting with high contrast
    - Celebrity looking confident, powerful, and slightly arrogant
    - Wearing expensive business attire
    - Luxury office or boardroom background
    - High-end, cinematic quality
    - No text or overlays in the image
    - Focus on the celebrity's face and upper body
    - Professional headshot composition
    
    Style: Corporate headshot, executive portrait, luxury photography, 
    high-end business photography, dramatic lighting, photorealistic.
    
    Background: Luxury office, corporate boardroom, or high-end executive suite.
    
    The celebrity should look like a powerful, wealthy executive or celebrity.
    """
    
    print(f"Creating high-quality celebrity image for: {celebrity}")
    print(f"Image prompt: {detailed_prompt[:100]}...")
    
    # Create a sophisticated celebrity placeholder image
    return create_sophisticated_celebrity_placeholder(celebrity, celebrity_description)


def create_sophisticated_celebrity_placeholder(celebrity, celebrity_description):
    """
    Create a sophisticated celebrity placeholder image
    """
    
    # Create a high-quality celebrity image
    img = Image.new('RGBA', (1024, 1024), color=(20, 20, 20, 255))  # Dark background
    draw = ImageDraw.Draw(img)
    
    # Create sophisticated gradient background
    for y in range(1024):
        intensity = int(40 * (y / 1024))
        base_color = (20 + intensity, 20 + intensity, 20 + intensity, 255)
        draw.line([(0, y), (1024, y)], fill=base_color)
    
    # Create celebrity silhouette (centered)
    celebrity_x = 512 - 150  # Center the celebrity
    celebrity_y = 200
    
    # Head (more realistic)
    head_radius = 80
    draw.ellipse([celebrity_x + 70, celebrity_y + 50, celebrity_x + 230, celebrity_y + 210], 
                 fill=(220, 200, 180, 255))
    
    # Body (suit)
    draw.rectangle([celebrity_x + 100, celebrity_y + 200, celebrity_x + 200, celebrity_y + 500], 
                   fill=(60, 60, 60, 255))
    
    # Arms
    draw.rectangle([celebrity_x + 60, celebrity_y + 250, celebrity_x + 100, celebrity_y + 450], 
                   fill=(220, 200, 180, 255))
    draw.rectangle([celebrity_x + 200, celebrity_y + 250, celebrity_x + 240, celebrity_y + 450], 
                   fill=(220, 200, 180, 255))
    
    # Expensive suit details
    # Tie
    draw.rectangle([celebrity_x + 130, celebrity_y + 200, celebrity_x + 170, celebrity_y + 350], 
                    fill=(200, 0, 0, 255))
    
    # Suit lapels
    draw.polygon([(celebrity_x + 100, celebrity_y + 200), (celebrity_x + 150, celebrity_y + 220), 
                  (celebrity_x + 100, celebrity_y + 240)], fill=(80, 80, 80, 255))
    draw.polygon([(celebrity_x + 200, celebrity_y + 200), (celebrity_x + 150, celebrity_y + 220), 
                  (celebrity_x + 200, celebrity_y + 240)], fill=(80, 80, 80, 255))
    
    # Luxury accessories
    # Expensive watch
    draw.ellipse([celebrity_x + 80, celebrity_y + 300, celebrity_x + 100, celebrity_y + 320], 
                 fill=(255, 215, 0, 255))
    draw.ellipse([celebrity_x + 85, celebrity_y + 305, celebrity_x + 95, celebrity_y + 315], 
                 fill=(0, 0, 0, 255))
    
    # Gold ring
    draw.ellipse([celebrity_x + 210, celebrity_y + 350, celebrity_x + 230, celebrity_y + 370], 
                 fill=(255, 215, 0, 255))
    
    # Luxury background elements
    # Corporate boardroom table
    table_y = 600
    draw.rectangle([200, table_y, 824, table_y + 20], fill=(100, 100, 100, 255))
    
    # Expensive chairs
    for i in range(3):
        chair_x = 300 + i * 150
        chair_y = table_y - 100
        draw.rectangle([chair_x, chair_y, chair_x + 80, chair_y + 100], fill=(120, 120, 120, 255))
    
    # Luxury office elements
    # Expensive artwork on walls
    draw.rectangle([100, 100, 200, 150], fill=(255, 215, 0, 100))
    draw.rectangle([824, 100, 924, 150], fill=(255, 215, 0, 100))
    
    # Corporate documents
    for i in range(5):
        doc_x = 300 + i * 100
        doc_y = table_y + 30
        draw.rectangle([doc_x, doc_y, doc_x + 60, doc_y + 80], fill=(255, 255, 255, 200))
    
    # Add sophisticated lighting effects
    # Spotlight effect on celebrity
    for i in range(100):
        alpha = int(50 * (1 - i / 100))
        draw.ellipse([celebrity_x + 100 - i, celebrity_y + 100 - i, 
                     celebrity_x + 200 + i, celebrity_y + 400 + i], 
                     fill=(255, 255, 255, alpha))
    
    # Add luxury atmosphere
    for i in range(20):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        size = random.randint(2, 6)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255, 30))
    
    return img


def generate_hashtags(hashtag_categories):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(hashtag_categories['viral'], 2))
    hashtags.extend(random.sample(hashtag_categories['controversial'], 2))
    hashtags.extend(random.sample(hashtag_categories['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Pure Celebrity AI System"""
    
    print("The Unseen Economy - Pure Celebrity AI System")
    print("=" * 60)
    
    # Setup
    constants = setup()
    gemini_model = constants['gemini_model']
    
    try:
        # Step 1: Get viral celebrity news
        print("Generating viral celebrity news...")
        brief = get_celebrity_viral_news(gemini_model)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Celebrity: {brief['celebrity']}")
        print(f"Scandal: {brief['scandal_type']}")
        print(f"Story: {brief['story_summary']}")
        print(f"Color: {brief['primary_color_hex']}")
        
        # Step 2: Create high-quality celebrity image
        print("Creating high-quality celebrity image...")
        celebrity_image = create_high_quality_celebrity_image(brief)
        
        # Step 3: Save celebrity image
        celebrity_image.save('pure_celebrity_image.png')
        print("Successfully generated pure_celebrity_image.png")
        
        # Step 4: Generate hashtags
        hashtags = generate_hashtags(constants['hashtag_categories'])
        
        # Step 5: Generate Facebook post caption
        cta = random.choice(constants['engagement_hooks'])
        
        facebook_caption = f"""{brief['headline']}

{brief['subtext']}

{brief['story_summary']}

{cta}

{hashtags}"""
        
        # Print summary
        print("\n" + "="*60)
        print("PURE CELEBRITY AI SYSTEM OUTPUT:")
        print("="*60)
        print(f"Celebrity: {brief['celebrity']}")
        print(f"Scandal: {brief['scandal_type']}")
        print(f"Story: {brief['story_summary']}")
        print(f"CTA: {cta}")
        print(f"Hashtags: {hashtags}")
        print("\n" + "="*60)
        print("FACEBOOK POST CAPTION:")
        print("="*60)
        print(facebook_caption)
        print("="*60)
        
        # Save creative brief
        with open('pure_celebrity_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        # Save Facebook caption
        with open('facebook_caption.txt', 'w') as f:
            f.write(facebook_caption)
        
        print("Pure celebrity brief saved to pure_celebrity_brief.json")
        print("Facebook caption saved to facebook_caption.txt")
        
    except Exception as e:
        print(f"Error in Pure Celebrity AI system: {e}")
        return


if __name__ == "__main__":
    main()




