#!/usr/bin/env python3
"""
The Unseen Economy - Gemini Content Pipeline
Uses Google Gemini AI for viral content generation
"""

import os
import random
import json
import requests
import io
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai


def setup():
    """Initialize all constants and Gemini client"""
    
    # Engagement hooks for CTA banners
    ENGAGEMENT_HOOKS = [
        'SHARE IF THIS MAKES YOU ANGRY',
        'SHARE IF YOU\'RE TIRED OF BEING BLAMED',
        'SHARE IF YOU\'RE READY FOR CHANGE',
        'SHARE IF YOU\'RE FED UP',
        'SHARE IF THIS SHOCKS YOU',
        'SHARE IF YOU\'RE ANGRY',
        'SHARE IF YOU\'RE FRUSTRATED',
        'SHARE IF YOU\'RE READY TO FIGHT'
    ]
    
    # Hashtag categories for Facebook post text
    HASHTAG_CATEGORIES = {
        'viral': ['#ViralTake', '#TruthBomb', '#DataBomb', '#MindBlown'],
        'controversial': ['#EconomicReality', '#WealthInequality', '#CorporateGreed'],
        'problem_focused': ['#HousingCrisis', '#DebtCrisis', '#Healthcare', '#GigEconomy']
    }
    
    # Image dimensions
    IMG_WIDTH = 1024
    IMG_HEIGHT = 1024
    
    # Configure Gemini
    genai.configure(api_key="AIzaSyBt2KV8_nOKdpG14Pf92CT1-8L48dUZk2o")
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'img_width': IMG_WIDTH,
        'img_height': IMG_HEIGHT,
        'model': genai.GenerativeModel('gemini-2.5-flash')
    }


def generate_viral_take(model):
    """Generate a viral economic take using Gemini AI"""
    
    prompt = """You generate content for 'The Unseen Economy' page. Create a viral economic take as a JSON object with two keys: headline (the main shocking statement) and subtext (the 'medieval serfdom' style punchline). Target: US/EU Millennials on economic inequality.

The headline should be provocative and shocking (under 60 characters).
The subtext should be a punchy follow-up that adds impact (under 80 characters).

Focus on themes like:
- Wealth inequality
- Corporate greed
- Gig economy exploitation
- Housing crisis
- Healthcare costs
- Student debt
- Wage stagnation

Make it angry, provocative, and designed to go viral.

Return ONLY a valid JSON object with 'headline' and 'subtext' keys."""
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up the response to extract JSON
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        take = json.loads(content)
        return take
    
    except Exception as e:
        print(f"Error generating viral take with Gemini: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        # Fallback content
        return {
            'headline': 'The gig economy isn\'t the future of work',
            'subtext': '- it\'s the return of medieval serfdom with better marketing.'
        }


def generate_image_prompt(theme_description, model):
    """Generate DALL-E 3 prompt for background image using Gemini"""
    
    prompt = f"""You are a creative director. Create a DALL-E 3 prompt for a background graphic or symbolic asset. This image will have text overlaid on it later. It must be abstract, minimalist, or symbolic, look professional, and be text-free. The style should be high-end: neo-brutalist, abstract data-art, or surreal photorealism. High contrast, dark, and cinematic.

The image should symbolically represent the economic theme: {theme_description}

Return ONLY the DALL-E 3 prompt text, no explanations."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        print(f"Error generating image prompt with Gemini: {e}")
        return "A dark, neo-brutalist composition with stark geometric shapes and high contrast. Abstract representation of economic inequality with dramatic shadows and cinematic lighting. Professional, minimalist, text-free background."


def create_demo_background():
    """Create a demo background image"""
    
    # Create a dark, professional background
    img = Image.new('RGBA', (1024, 1024), color=(20, 20, 20, 255))
    draw = ImageDraw.Draw(img)
    
    # Add geometric elements
    # Draw diagonal lines
    for i in range(0, 1024, 50):
        draw.line([(i, 0), (i + 100, 1024)], fill=(40, 40, 40, 255), width=2)
    
    # Add corner accents
    corner_size = 80
    draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(1024, 0), (1024 - corner_size, 0), (1024, corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(0, 1024), (corner_size, 1024), (0, 1024 - corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(1024, 1024), (1024 - corner_size, 1024), (1024, 1024 - corner_size)], fill=(255, 68, 68, 255))
    
    # Add data visualization bars
    bar_width = 20
    bar_spacing = 30
    start_x = 50
    start_y = 1024 - 100
    
    bars = [5, 8, 12, 20, 35, 80, 200]  # Heights representing wealth distribution
    
    for i, bar_height in enumerate(bars):
        x = start_x + (i * (bar_width + bar_spacing))
        y = start_y - bar_height
        
        if bar_height > 50:
            color = (255, 68, 68, 255)  # Red for high wealth
        elif bar_height > 20:
            color = (255, 170, 68, 255)  # Orange for medium wealth
        else:
            color = (68, 68, 68, 255)  # Gray for low wealth
        
        draw.rectangle([x, y, x + bar_width, start_y], fill=color)
    
    return img


def create_professional_post(base_image, headline, subtext, cta_text):
    """Create professional post with text overlay"""
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Try to load professional fonts
    try:
        # Try different font paths
        headline_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 80)
        subtext_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
        cta_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
    except:
        try:
            headline_font = ImageFont.truetype("arial.ttf", 80)
            subtext_font = ImageFont.truetype("arial.ttf", 40)
            cta_font = ImageFont.truetype("arial.ttf", 36)
        except:
            print("Using default fonts")
            headline_font = ImageFont.load_default()
            subtext_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
    
    # Get image dimensions
    img_width, img_height = final_image.size
    
    # Draw headline
    headline_bbox = draw.textbbox((0, 0), headline, font=headline_font)
    headline_width = headline_bbox[2] - headline_bbox[0]
    headline_height = headline_bbox[3] - headline_bbox[1]
    
    headline_x = (img_width - headline_width) // 2
    headline_y = img_height // 2 - 100
    
    # Draw headline with stroke for readability
    draw.text((headline_x, headline_y), headline, font=headline_font, fill='white', 
              stroke_width=3, stroke_fill='black')
    
    # Draw subtext
    subtext_bbox = draw.textbbox((0, 0), subtext, font=subtext_font)
    subtext_width = subtext_bbox[2] - subtext_bbox[0]
    subtext_height = subtext_bbox[3] - subtext_bbox[1]
    
    subtext_x = (img_width - subtext_width) // 2
    subtext_y = headline_y + headline_height + 20
    
    # Draw subtext with stroke
    draw.text((subtext_x, subtext_y), subtext, font=subtext_font, fill=(200, 200, 200), 
              stroke_width=2, stroke_fill='black')
    
    # Create CTA banner
    banner_height = 100
    banner_y = img_height - banner_height
    
    # Draw red banner background
    draw.rectangle([0, banner_y, img_width, img_height], fill='red')
    
    # Draw CTA text
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    cta_height = cta_bbox[3] - cta_bbox[1]
    
    cta_x = (img_width - cta_width) // 2
    cta_y = banner_y + (banner_height - cta_height) // 2
    
    # Draw CTA text with stroke
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill='white', 
              stroke_width=2, stroke_fill='black')
    
    return final_image


def generate_hashtags(constants):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(constants['hashtag_categories']['viral'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['controversial'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Main orchestrator function with Gemini AI"""
    
    print("The Unseen Economy - Gemini Content Pipeline")
    print("=" * 60)
    
    # Setup
    constants = setup()
    model = constants['model']
    
    try:
        # Step 1: Generate viral take with Gemini
        print("Generating viral take with Gemini AI...")
        take = generate_viral_take(model)
        print(f"Headline: {take['headline']}")
        print(f"Subtext: {take['subtext']}")
        
        # Step 2: Generate image prompt with Gemini
        print("Creating image prompt with Gemini...")
        theme = take['headline'] + ' ' + take['subtext']
        img_prompt = generate_image_prompt(theme, model)
        print(f"Image prompt: {img_prompt[:100]}...")
        
        # Step 3: Create demo background
        print("Creating demo background...")
        base_img = create_demo_background()
        
        # Step 4: Create professional post
        print("Creating professional post...")
        cta = random.choice(constants['engagement_hooks'])
        final_image = create_professional_post(base_img, take['headline'], take['subtext'], cta)
        
        # Step 5: Save final image
        final_image.save('gemini_final_post.png')
        print("Successfully generated gemini_final_post.png")
        
        # Step 6: Generate hashtags
        hashtags = generate_hashtags(constants)
        
        # Print content for Facebook post
        print("\n" + "="*60)
        print("GEMINI-GENERATED CONTENT FOR FACEBOOK POST:")
        print("="*60)
        print(f"Headline: {take['headline']}")
        print(f"Subtext: {take['subtext']}")
        print(f"CTA: {cta}")
        print(f"Hashtags: {hashtags}")
        print("="*60)
        
        # Save content to file
        content_data = {
            'headline': take['headline'],
            'subtext': take['subtext'],
            'cta': cta,
            'hashtags': hashtags,
            'image_prompt': img_prompt,
            'ai_model': 'gemini-pro'
        }
        
        with open('gemini_content_data.json', 'w') as f:
            json.dump(content_data, f, indent=2)
        
        print("Content data saved to gemini_content_data.json")
        
    except Exception as e:
        print(f"Error in Gemini pipeline: {e}")
        return


if __name__ == "__main__":
    main()
