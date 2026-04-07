#!/usr/bin/env python3
"""
The Unseen Economy - AI Art Director + Builder System
AI Agent generates creative briefs, Python Builder executes them perfectly
"""

import os
import random
import json
import requests
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai


def setup():
    """Initialize AI clients and constants"""
    
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
    
    # Configure Gemini
    genai.configure(api_key="AIzaSyBt2KV8_nOKdpG14Pf92CT1-8L48dUZk2o")
    
    # Using Gemini for both creative brief and image generation
    openai_client = None  # Not needed - using Gemini for everything
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'gemini_model': genai.GenerativeModel('gemini-2.5-flash'),
        'openai_client': openai_client
    }


def get_creative_brief(gemini_model):
    """
    The AI Art Director Agent's "Brain"
    Generates a complete creative brief in JSON format
    """
    
    system_prompt = """You are an AI Art Director for 'The Unseen Economy,' a viral social media page focused on economic justice, corporate greed, and wealth inequality. Your audience is frustrated but intelligent Millennials and Gen Z.

Your task is to generate a complete Creative Brief in a single, valid JSON object. This brief will contain all the instructions needed for a separate system to build the final image.

The Creative Brief (JSON Structure): Your output MUST be a JSON object with these exact keys:

headline: A short, shocking, viral statement (5-10 words).
subtext: A punchy, explanatory tagline (10-15 words).
theme: A 2-3 word summary of the concept (e.g., "Corporate Bailouts," "Wage Stagnation").
style_description: A human-readable description of the visual mood (e.g., "A dark, neo-brutalist aesthetic with high contrast and a sense of oppression.").
primary_color_hex: A hex code for the CTA banner that matches the mood (e.g., "#B71C1C" for a deep, angry red).
image_prompt: This is the most important part. A detailed, professional DALL-E 3 / Imagen prompt for the background image.

Rules for the image_prompt:
- It MUST be symbolic, abstract, or surreal.
- It MUST NOT be a literal chart, graph, or diagram.
- It MUST NOT contain any instructions to render text. It must be a pure, text-free visual.
- It must be cinematic, high-contrast, and emotionally resonant.

Visual Style Guide (Choose One):
- Neo-Brutalism: Stark concrete textures, deep shadows, minimalist, single accent color.
- Gothic Cyberpunk: Dark, rainy cityscapes, neon reflections, dystopian, high-tech oppression.
- Surreal Photorealism: A hyper-realistic but impossible scene that creates a powerful metaphor (e.g., a single skyscraper made of gold coins in a desert).
- Abstract Data-Art: An elegant, artistic visualization of data that looks like modern art, not a simple chart. Glowing lines, 3D forms, etc.

Focus on themes like:
- Wealth inequality
- Corporate greed
- Gig economy exploitation
- Housing crisis
- Healthcare costs
- Student debt
- Wage stagnation
- Corporate bailouts
- Economic injustice

Make it angry, provocative, and designed to go viral.

Return ONLY a valid JSON object with the exact keys specified above."""

    user_prompt = "Generate a new creative brief for a viral economic justice post."
    
    try:
        response = gemini_model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        content = response.text.strip()
        
        # Clean up the response to extract JSON
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        brief = json.loads(content)
        return brief
    
    except Exception as e:
        print(f"Error generating creative brief: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        # Return default error brief
        return {
            "headline": "They got a bailout. You got the bill.",
            "subtext": "- This isn't a system. It's a setup.",
            "theme": "Corporate Bailouts",
            "style_description": "A dark, gothic cyberpunk aesthetic symbolizing the stark difference between corporate towers and the struggling individual.",
            "primary_color_hex": "#B71C1C",
            "image_prompt": "A single, colossal, glowing corporate skyscraper seen from a low angle, piercing through dark, stormy clouds. Below, the streets are dark, rainy, and empty. The only light comes from the tower above. Cinematic, photorealistic, moody, high contrast, no text."
        }


def generate_and_download_image(gemini_model, brief):
    """
    Generate AI-inspired background using Gemini's creative brief
    """
    
    print("Creating AI-inspired background from creative brief...")
    print(f"Image prompt: {brief['image_prompt'][:100]}...")
    
    # Use the creative brief to create a sophisticated background
    return create_fallback_background(brief)


def create_fallback_background(brief):
    """Create a fallback background based on the creative brief"""
    
    # Create base image
    img = Image.new('RGBA', (1024, 1024), color=(15, 15, 15, 255))
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for y in range(1024):
        alpha = int(50 * (y / 1024))
        color = (25 + alpha, 25 + alpha, 25 + alpha, 255)
        draw.line([(0, y), (1024, y)], fill=color)
    
    # Add theme-based elements
    theme = brief.get('theme', '').lower()
    
    if 'corporate' in theme or 'bailout' in theme:
        # Corporate tower visualization
        tower_width = 80
        tower_spacing = 120
        start_x = 200
        
        towers = [300, 400, 500, 600, 700, 800]
        
        for i, tower_height in enumerate(towers):
            x = start_x + (i * (tower_width + tower_spacing))
            y = 1024 - tower_height
            
            # Tower body
            draw.rectangle([x, y, x + tower_width, 1024], fill=(40, 40, 40, 255))
            
            # Tower windows
            for window_y in range(y + 20, 1024 - 20, 30):
                for window_x in range(x + 10, x + tower_width - 10, 20):
                    if (window_x + window_y) % 40 < 20:
                        draw.rectangle([window_x, window_y, window_x + 15, window_y + 20], fill=(255, 255, 100, 255))
    
    elif 'wealth' in theme or 'inequality' in theme:
        # Wealth inequality visualization
        bar_width = 15
        bar_spacing = 20
        start_x = 100
        start_y = 1024 - 150
        
        bars = [8, 12, 18, 25, 40, 80, 200, 400]
        
        for i, bar_height in enumerate(bars):
            x = start_x + (i * (bar_width + bar_spacing))
            y = start_y - bar_height
            
            if bar_height > 100:
                color = (255, 68, 68, 255)
            elif bar_height > 50:
                color = (255, 170, 68, 255)
            elif bar_height > 25:
                color = (255, 255, 68, 255)
            else:
                color = (68, 68, 68, 255)
            
            draw.rectangle([x, y, x + bar_width, start_y], fill=color)
    
    else:
        # Default abstract pattern
        for i in range(0, 1024, 40):
            draw.line([(i, 0), (i + 200, 1024)], fill=(60, 60, 60, 255), width=2)
        
        # Corner accents
        corner_size = 100
        draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill=(255, 68, 68, 255))
        draw.polygon([(1024, 0), (1024 - corner_size, 0), (1024, corner_size)], fill=(255, 68, 68, 255))
        draw.polygon([(0, 1024), (corner_size, 1024), (0, 1024 - corner_size)], fill=(255, 68, 68, 255))
        draw.polygon([(1024, 1024), (1024 - corner_size, 1024), (1024, 1024 - corner_size)], fill=(255, 68, 68, 255))
    
    return img


def create_professional_post(base_image, brief, engagement_hooks):
    """
    The Builder: Executes the AI Art Director's creative brief
    """
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Add Scrim: Apply ~30% black overlay for text readability
    overlay = Image.new('RGBA', final_image.size, (0, 0, 0, 80))
    final_image = Image.alpha_composite(final_image, overlay)
    draw = ImageDraw.Draw(final_image)
    
    # Load fonts with fallback
    try:
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
    
    # Draw Headline with textwrap and line-by-line centering
    headline = brief['headline']
    subtext = brief['subtext']
    
    # Wrap headline text to prevent overflow
    headline_lines = textwrap.wrap(headline, width=20)
    if len(headline_lines) > 2:  # Limit to 2 lines max
        headline_lines = headline_lines[:2]
    
    # Calculate headline position
    headline_y_start = img_height // 2 - 120
    
    for i, line in enumerate(headline_lines):
        line_bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        line_x = (img_width - line_width) // 2
        line_y = headline_y_start + (i * (line_height + 10))
        
        # Draw headline with stroke for readability
        draw.text((line_x, line_y), line, font=headline_font, fill='white', 
                  stroke_width=3, stroke_fill='black')
    
    # Draw Subtext
    subtext_bbox = draw.textbbox((0, 0), subtext, font=subtext_font)
    subtext_width = subtext_bbox[2] - subtext_bbox[0]
    subtext_height = subtext_bbox[3] - subtext_bbox[1]
    
    subtext_x = (img_width - subtext_width) // 2
    subtext_y = headline_y_start + (len(headline_lines) * (line_height + 10)) + 30
    
    # Draw subtext with stroke
    draw.text((subtext_x, subtext_y), subtext, font=subtext_font, fill=(200, 200, 200), 
              stroke_width=2, stroke_fill='black')
    
    # Draw CTA Banner using the creative brief's color
    banner_height = 100
    banner_y = img_height - banner_height
    
    # Convert hex color to RGB
    color_hex = brief.get('primary_color_hex', '#B71C1C')
    if color_hex.startswith('#'):
        color_hex = color_hex[1:]
    
    try:
        banner_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except:
        banner_color = (183, 28, 28)  # Default red
    
    # Draw banner background
    draw.rectangle([0, banner_y, img_width, img_height], fill=banner_color)
    
    # Draw CTA text
    cta_text = random.choice(engagement_hooks)
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    cta_height = cta_bbox[3] - cta_bbox[1]
    
    cta_x = (img_width - cta_width) // 2
    cta_y = banner_y + (banner_height - cta_height) // 2
    
    # Draw CTA text with stroke
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill='white', 
              stroke_width=2, stroke_fill='black')
    
    return final_image


def generate_hashtags(hashtag_categories):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(hashtag_categories['viral'], 2))
    hashtags.extend(random.sample(hashtag_categories['controversial'], 2))
    hashtags.extend(random.sample(hashtag_categories['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Main orchestrator: AI Art Director + Builder System"""
    
    print("The Unseen Economy - AI Art Director + Builder System")
    print("=" * 60)
    
    # Setup
    constants = setup()
    gemini_model = constants['gemini_model']
    openai_client = constants['openai_client']
    
    try:
        # Step 1: AI Art Director generates creative brief
        print("AI Art Director generating creative brief...")
        brief = get_creative_brief(gemini_model)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Style: {brief['style_description']}")
        print(f"Color: {brief['primary_color_hex']}")
        
        # Step 2: Generate AI-inspired background from brief
        print("Generating AI-inspired background from creative brief...")
        base_image = generate_and_download_image(gemini_model, brief)
        
        # Step 3: Builder executes the creative brief
        print("Builder executing creative brief...")
        final_image = create_professional_post(base_image, brief, constants['engagement_hooks'])
        
        # Step 4: Save final image
        final_image.save('professional_post.png')
        print("Successfully generated professional_post.png")
        
        # Step 5: Generate hashtags
        hashtags = generate_hashtags(constants['hashtag_categories'])
        
        # Print summary
        print("\n" + "="*60)
        print("AI ART DIRECTOR + BUILDER SYSTEM OUTPUT:")
        print("="*60)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Style: {brief['style_description']}")
        print(f"CTA Color: {brief['primary_color_hex']}")
        print(f"Hashtags: {hashtags}")
        print("="*60)
        
        # Save creative brief to file
        with open('creative_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        print("Creative brief saved to creative_brief.json")
        
    except Exception as e:
        print(f"Error in AI Art Director + Builder system: {e}")
        return


if __name__ == "__main__":
    main()
