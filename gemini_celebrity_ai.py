#!/usr/bin/env python3
"""
The Unseen Economy - Gemini Celebrity AI System
Uses Gemini AI to generate REAL celebrity images
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
        'viral': ['#ViralNews', '#BreakingNews', '#Trending', '#NowTrending'],
        'controversial': ['#Scandal', '#Outrage', '#Shocking', '#Exposed'],
        'problem_focused': ['#EconomicReality', '#WealthInequality', '#CorporateGreed', '#Truth']
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


def generate_gemini_celebrity_image(brief, gemini_model):
    """
    Generate a REAL celebrity image using Gemini AI image generation
    """
    
    celebrity = brief.get('celebrity', 'Celebrity')
    celebrity_description = brief.get('celebrity_description', 'A celebrity')
    image_prompt = brief.get('image_prompt', '')
    
    # Create a detailed prompt for celebrity image generation
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
    
    print(f"Generating REAL celebrity image using Gemini AI for: {celebrity}")
    print(f"Image prompt: {detailed_prompt[:100]}...")
    
    try:
        # Use Gemini to generate the image
        response = gemini_model.generate_content(detailed_prompt)
        
        # Check if Gemini can generate images
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Gemini generated an image
                    image_data = part.inline_data.data
                    image = Image.open(io.BytesIO(image_data))
                    return image
        
        # If no image generated, create a sophisticated placeholder
        print("Gemini did not generate an image, creating sophisticated placeholder...")
        return create_sophisticated_celebrity_placeholder(celebrity, celebrity_description)
        
    except Exception as e:
        print(f"Error generating Gemini celebrity image: {e}")
        print("Creating sophisticated placeholder...")
        return create_sophisticated_celebrity_placeholder(celebrity, celebrity_description)


def create_sophisticated_celebrity_placeholder(celebrity, celebrity_description):
    """
    Create a sophisticated celebrity placeholder using advanced techniques
    """
    
    # Create a high-quality celebrity image
    img = Image.new('RGBA', (1024, 1024), color=(5, 5, 5, 255))  # Very dark background
    draw = ImageDraw.Draw(img)
    
    # Create sophisticated gradient background
    for y in range(1024):
        intensity = int(120 * (y / 1024))
        base_color = (5 + intensity, 5 + intensity, 5 + intensity, 255)
        draw.line([(0, y), (1024, y)], fill=base_color)
    
    # Create celebrity silhouette (centered and larger)
    celebrity_x = 512 - 350  # Center the celebrity
    celebrity_y = 50
    
    # Head (more realistic with shading)
    head_radius = 200
    # Main head
    draw.ellipse([celebrity_x + 150, celebrity_y + 150, celebrity_x + 550, celebrity_y + 550], 
                 fill=(220, 200, 180, 255))
    
    # Head shading
    draw.ellipse([celebrity_x + 170, celebrity_y + 170, celebrity_x + 530, celebrity_y + 530], 
                 fill=(200, 180, 160, 255))
    
    # Hair
    draw.ellipse([celebrity_x + 130, celebrity_y + 130, celebrity_x + 570, celebrity_y + 400], 
                 fill=(80, 60, 40, 255))
    
    # Eyes
    draw.ellipse([celebrity_x + 250, celebrity_y + 300, celebrity_x + 290, celebrity_y + 340], 
                 fill=(0, 0, 0, 255))
    draw.ellipse([celebrity_x + 410, celebrity_y + 300, celebrity_x + 450, celebrity_y + 340], 
                 fill=(0, 0, 0, 255))
    
    # Nose
    draw.ellipse([celebrity_x + 340, celebrity_y + 380, celebrity_x + 360, celebrity_y + 420], 
                 fill=(200, 180, 160, 255))
    
    # Mouth
    draw.ellipse([celebrity_x + 320, celebrity_y + 440, celebrity_x + 380, celebrity_y + 460], 
                 fill=(150, 100, 100, 255))
    
    # Body (expensive suit)
    draw.rectangle([celebrity_x + 200, celebrity_y + 550, celebrity_x + 500, celebrity_y + 850], 
                   fill=(40, 40, 40, 255))
    
    # Arms
    draw.rectangle([celebrity_x + 150, celebrity_y + 600, celebrity_x + 200, celebrity_y + 800], 
                   fill=(220, 200, 180, 255))
    draw.rectangle([celebrity_x + 500, celebrity_y + 600, celebrity_x + 550, celebrity_y + 800], 
                   fill=(220, 200, 180, 255))
    
    # Expensive suit details
    # Tie
    draw.rectangle([celebrity_x + 320, celebrity_y + 550, celebrity_x + 380, celebrity_y + 750], 
                    fill=(200, 0, 0, 255))
    
    # Suit lapels
    draw.polygon([(celebrity_x + 200, celebrity_y + 550), (celebrity_x + 350, celebrity_y + 590), 
                  (celebrity_x + 200, celebrity_y + 630)], fill=(60, 60, 60, 255))
    draw.polygon([(celebrity_x + 500, celebrity_y + 550), (celebrity_x + 350, celebrity_y + 590), 
                  (celebrity_x + 500, celebrity_y + 630)], fill=(60, 60, 60, 255))
    
    # Luxury accessories
    # Expensive watch
    draw.ellipse([celebrity_x + 170, celebrity_y + 700, celebrity_x + 210, celebrity_y + 740], 
                 fill=(255, 215, 0, 255))
    draw.ellipse([celebrity_x + 180, celebrity_y + 710, celebrity_x + 200, celebrity_y + 730], 
                 fill=(0, 0, 0, 255))
    
    # Gold ring
    draw.ellipse([celebrity_x + 520, celebrity_y + 750, celebrity_x + 540, celebrity_y + 770], 
                 fill=(255, 215, 0, 255))
    
    # Luxury background elements
    # Corporate boardroom table
    table_y = 900
    draw.rectangle([200, table_y, 824, table_y + 60], fill=(100, 100, 100, 255))
    
    # Expensive chairs
    for i in range(3):
        chair_x = 300 + i * 150
        chair_y = table_y - 200
        draw.rectangle([chair_x, chair_y, chair_x + 160, chair_y + 200], fill=(120, 120, 120, 255))
    
    # Luxury office elements
    # Expensive artwork on walls
    draw.rectangle([100, 100, 200, 350], fill=(255, 215, 0, 150))
    draw.rectangle([824, 100, 924, 350], fill=(255, 215, 0, 150))
    
    # Corporate documents
    for i in range(5):
        doc_x = 300 + i * 100
        doc_y = table_y + 70
        draw.rectangle([doc_x, doc_y, doc_x + 140, doc_y + 160], fill=(255, 255, 255, 200))
    
    # Add sophisticated lighting effects
    # Spotlight effect on celebrity
    for i in range(300):
        alpha = int(150 * (1 - i / 300))
        draw.ellipse([celebrity_x + 200 - i, celebrity_y + 200 - i, 
                     celebrity_x + 500 + i, celebrity_y + 800 + i], 
                     fill=(255, 255, 255, alpha))
    
    # Add luxury atmosphere
    for i in range(60):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        size = random.randint(6, 15)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255, 80))
    
    # Add professional photography effects
    # Vignette effect
    for i in range(350):
        alpha = int(180 * (i / 350))
        draw.ellipse([i, i, 1024 - i, 1024 - i], fill=(0, 0, 0, alpha))
    
    return img


def generate_hashtags(hashtag_categories):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(hashtag_categories['viral'], 2))
    hashtags.extend(random.sample(hashtag_categories['controversial'], 2))
    hashtags.extend(random.sample(hashtag_categories['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Gemini Celebrity AI System"""
    
    print("The Unseen Economy - Gemini Celebrity AI System")
    print("=" * 60)
    print("Using Gemini AI to generate REAL celebrity images")
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
        
        # Step 2: Generate REAL celebrity image using Gemini
        print("Generating REAL celebrity image using Gemini AI...")
        celebrity_image = generate_gemini_celebrity_image(brief, gemini_model)
        
        # Step 3: Save celebrity image
        celebrity_image.save('gemini_celebrity_image.png')
        print("Successfully generated gemini_celebrity_image.png")
        
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
        print("GEMINI CELEBRITY AI SYSTEM OUTPUT:")
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
        with open('gemini_celebrity_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        # Save Facebook caption
        with open('facebook_caption.txt', 'w') as f:
            f.write(facebook_caption)
        
        print("Gemini celebrity brief saved to gemini_celebrity_brief.json")
        print("Facebook caption saved to facebook_caption.txt")
        
    except Exception as e:
        print(f"Error in Gemini Celebrity AI system: {e}")
        return


if __name__ == "__main__":
    main()




