#!/usr/bin/env python3
"""
The Unseen Economy - Advanced AI Director System
Uses Gemini AI to create truly unique, sophisticated backgrounds
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
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'gemini_model': genai.GenerativeModel('gemini-2.5-flash')
    }


def get_creative_brief(gemini_model):
    """
    Advanced AI Art Director - Generates sophisticated creative briefs
    """
    
    system_prompt = """You are an elite AI Art Director for 'The Unseen Economy,' a viral social media page. You create sophisticated, cinematic visual concepts that are both symbolic and emotionally powerful.

Your task: Generate a complete Creative Brief in JSON format with these exact keys:

headline: A shocking, viral statement (5-10 words max)
subtext: A punchy tagline (10-15 words max)  
theme: 2-3 word concept summary
style_description: Detailed visual mood description
primary_color_hex: Hex color for CTA banner
visual_concept: A detailed description of the symbolic background design
background_elements: Specific visual elements to include
color_palette: Main colors for the background
mood_keywords: 3-5 words describing the emotional tone

Focus on themes like wealth inequality, corporate greed, economic injustice, housing crisis, wage stagnation.

Make it angry, provocative, and designed to go viral.

Return ONLY a valid JSON object."""

    user_prompt = "Generate a new creative brief for a viral economic justice post."
    
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
        print(f"Error generating creative brief: {e}")
        # Return sophisticated fallback
        return {
            "headline": "They own everything. You own nothing.",
            "subtext": "Welcome to the new feudalism. Your rent is their profit.",
            "theme": "Economic Feudalism",
            "style_description": "A dark, neo-brutalist aesthetic with stark contrasts and oppressive scale",
            "primary_color_hex": "#B71C1C",
            "visual_concept": "A massive, monolithic structure representing corporate power towering over a desolate landscape",
            "background_elements": ["geometric shapes", "dramatic shadows", "high contrast", "minimalist composition"],
            "color_palette": ["#1a1a1a", "#2d2d2d", "#ff4444", "#ffffff"],
            "mood_keywords": ["oppressive", "stark", "powerful", "unjust", "dystopian"]
        }


def create_sophisticated_background(brief):
    """
    Create a truly sophisticated, AI-inspired background based on the creative brief
    """
    
    # Create base image
    img = Image.new('RGBA', (1024, 1024), color=(26, 26, 26, 255))  # Dark base
    draw = ImageDraw.Draw(img)
    
    # Extract design elements from brief
    theme = brief.get('theme', '').lower()
    mood_keywords = brief.get('mood_keywords', ['oppressive', 'stark'])
    color_palette = brief.get('color_palette', ['#1a1a1a', '#2d2d2d', '#ff4444', '#ffffff'])
    background_elements = brief.get('background_elements', ['geometric shapes', 'dramatic shadows'])
    
    # Convert hex colors to RGB
    colors = []
    for color_hex in color_palette:
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        try:
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            colors.append(rgb)
        except:
            colors.append((255, 68, 68, 255))  # Default red
    
    # Create sophisticated gradient background
    for y in range(1024):
        # Create subtle gradient
        intensity = int(30 * (y / 1024))
        base_color = (26 + intensity, 26 + intensity, 26 + intensity, 255)
        draw.line([(0, y), (1024, y)], fill=base_color)
    
    # Add sophisticated geometric elements based on theme
    if 'wealth' in theme or 'inequality' in theme:
        create_wealth_inequality_visualization(draw, colors)
    elif 'corporate' in theme or 'greed' in theme:
        create_corporate_power_visualization(draw, colors)
    elif 'feudalism' in theme or 'rent' in theme:
        create_feudalism_visualization(draw, colors)
    elif 'housing' in theme or 'crisis' in theme:
        create_housing_crisis_visualization(draw, colors)
    else:
        create_abstract_oppression_visualization(draw, colors)
    
    # Add sophisticated texture overlay
    add_sophisticated_texture(draw)
    
    return img


def create_wealth_inequality_visualization(draw, colors):
    """Create sophisticated wealth inequality visualization"""
    
    # Create abstract wealth distribution
    bar_width = 20
    bar_spacing = 25
    start_x = 150
    start_y = 1024 - 200
    
    # Exponential wealth distribution
    bars = [15, 25, 40, 70, 120, 200, 350, 600]
    
    for i, bar_height in enumerate(bars):
        x = start_x + (i * (bar_width + bar_spacing))
        y = start_y - bar_height
        
        # Color based on wealth level
        if bar_height > 300:
            color = colors[2] if len(colors) > 2 else (255, 68, 68, 255)  # Red for extreme wealth
        elif bar_height > 150:
            color = (255, 170, 68, 255)  # Orange for high wealth
        elif bar_height > 75:
            color = (255, 255, 68, 255)  # Yellow for medium wealth
        else:
            color = (100, 100, 100, 255)  # Gray for low wealth
        
        # Draw bar with gradient effect
        for bar_y in range(y, start_y):
            alpha = int(255 * (1 - (bar_y - y) / bar_height))
            gradient_color = (*color[:3], alpha)
            draw.rectangle([x, bar_y, x + bar_width, bar_y + 1], fill=gradient_color)
        
        # Add subtle glow effect
        glow_color = (*color[:3], 50)
        draw.rectangle([x-2, y-2, x + bar_width + 2, start_y + 2], fill=glow_color)


def create_corporate_power_visualization(draw, colors):
    """Create sophisticated corporate power visualization"""
    
    # Create abstract corporate towers
    tower_width = 60
    tower_spacing = 100
    start_x = 200
    
    # Corporate towers of varying heights
    towers = [200, 300, 450, 600, 750, 900]
    
    for i, tower_height in enumerate(towers):
        x = start_x + (i * (tower_width + tower_spacing))
        y = 1024 - tower_height
        
        # Tower body with gradient
        for tower_y in range(y, 1024):
            intensity = int(100 * (1 - (tower_y - y) / tower_height))
            tower_color = (40 + intensity, 40 + intensity, 40 + intensity, 255)
            draw.rectangle([x, tower_y, x + tower_width, tower_y + 1], fill=tower_color)
        
        # Add sophisticated window patterns
        for window_y in range(y + 30, 1024 - 30, 40):
            for window_x in range(x + 10, x + tower_width - 10, 25):
                if (window_x + window_y) % 60 < 30:  # Sophisticated pattern
                    draw.rectangle([window_x, window_y, window_x + 20, window_y + 25], fill=(255, 255, 150, 255))
        
        # Add power lines/connections between towers
        if i < len(towers) - 1:
            next_x = start_x + ((i + 1) * (tower_width + tower_spacing))
            mid_y = 1024 - (tower_height + towers[i + 1]) // 2
            draw.line([(x + tower_width, mid_y), (next_x, mid_y)], fill=(255, 255, 100, 150), width=3)


def create_feudalism_visualization(draw, colors):
    """Create sophisticated feudalism visualization"""
    
    # Create abstract castle/manor house
    castle_x = 200
    castle_y = 1024 - 400
    castle_width = 200
    castle_height = 400
    
    # Castle base
    draw.rectangle([castle_x, castle_y, castle_x + castle_width, 1024], fill=(60, 60, 60, 255))
    
    # Castle towers
    tower_heights = [500, 450, 400, 500]
    for i, tower_height in enumerate(tower_heights):
        tower_x = castle_x + (i * 50)
        tower_y = 1024 - tower_height
        draw.rectangle([tower_x, tower_y, tower_x + 30, 1024], fill=(80, 80, 80, 255))
    
    # Serf huts (small, scattered)
    for i in range(8):
        hut_x = 600 + (i % 4) * 80
        hut_y = 1024 - 150 - (i // 4) * 100
        draw.rectangle([hut_x, hut_y, hut_x + 40, 1024], fill=(40, 40, 40, 255))
    
    # Add connecting lines (power structure)
    for i in range(4):
        line_x = castle_x + 100
        line_y = 1024 - 200
        hut_x = 600 + (i * 80)
        hut_y = 1024 - 100
        draw.line([(line_x, line_y), (hut_x, hut_y)], fill=(255, 100, 100, 100), width=2)


def create_housing_crisis_visualization(draw, colors):
    """Create sophisticated housing crisis visualization"""
    
    # Create abstract housing market
    # Expensive mansions (few, large)
    mansion_x = 100
    mansion_y = 1024 - 300
    draw.rectangle([mansion_x, mansion_y, mansion_x + 150, 1024], fill=(255, 200, 100, 255))
    
    # Affordable housing (many, small, scattered)
    for i in range(12):
        house_x = 400 + (i % 6) * 60
        house_y = 1024 - 120 - (i // 6) * 80
        house_color = (100, 100, 100, 255) if i % 3 == 0 else (150, 150, 150, 255)
        draw.rectangle([house_x, house_y, house_x + 40, 1024], fill=house_color)
    
    # Price tags floating above
    draw.text((mansion_x + 20, mansion_y - 30), "$2M+", fill=(255, 255, 255, 255))
    draw.text((500, 1024 - 150), "$500K", fill=(200, 200, 200, 255))


def create_abstract_oppression_visualization(draw, colors):
    """Create sophisticated abstract oppression visualization"""
    
    # Create abstract geometric oppression
    # Large oppressive shapes
    for i in range(3):
        shape_x = 200 + i * 200
        shape_y = 200 + i * 100
        shape_size = 150 + i * 50
        
        # Create abstract oppressive forms
        draw.ellipse([shape_x, shape_y, shape_x + shape_size, shape_y + shape_size], 
                     fill=(60, 60, 60, 200))
    
    # Add connecting oppressive lines
    for i in range(5):
        start_x = 100 + i * 150
        start_y = 300
        end_x = 200 + i * 150
        end_y = 800
        draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 100, 100, 150), width=4)


def add_sophisticated_texture(draw):
    """Add sophisticated texture overlay"""
    
    # Add subtle noise texture
    for i in range(0, 1024, 50):
        for j in range(0, 1024, 50):
            if (i + j) % 100 < 50:
                alpha = random.randint(10, 30)
                draw.rectangle([i, j, i + 25, j + 25], fill=(0, 0, 0, alpha))
    
    # Add subtle geometric patterns
    for i in range(0, 1024, 100):
        for j in range(0, 1024, 100):
            if (i + j) % 200 < 100:
                draw.rectangle([i, j, i + 30, j + 30], fill=(255, 255, 255, 5))


def create_professional_post(base_image, brief, engagement_hooks):
    """
    Create professional post with perfect text overlay
    """
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Add sophisticated scrim overlay
    overlay = Image.new('RGBA', final_image.size, (0, 0, 0, 100))
    final_image = Image.alpha_composite(final_image, overlay)
    draw = ImageDraw.Draw(final_image)
    
    # Load fonts
    try:
        headline_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 85)
        subtext_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 42)
        cta_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 38)
    except:
        try:
            headline_font = ImageFont.truetype("arial.ttf", 85)
            subtext_font = ImageFont.truetype("arial.ttf", 42)
            cta_font = ImageFont.truetype("arial.ttf", 38)
        except:
            headline_font = ImageFont.load_default()
            subtext_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
    
    # Get image dimensions
    img_width, img_height = final_image.size
    
    # Draw headline with perfect text wrapping
    headline = brief['headline']
    subtext = brief['subtext']
    
    # Wrap headline text to prevent overflow
    headline_lines = textwrap.wrap(headline, width=18)
    if len(headline_lines) > 2:
        headline_lines = headline_lines[:2]
    
    # Calculate headline position
    headline_y_start = img_height // 2 - 120
    
    for i, line in enumerate(headline_lines):
        line_bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        line_x = (img_width - line_width) // 2
        line_y = headline_y_start + (i * (line_height + 15))
        
        # Draw headline with sophisticated stroke
        draw.text((line_x, line_y), line, font=headline_font, fill='white', 
                  stroke_width=4, stroke_fill='black')
    
    # Draw subtext with perfect positioning
    subtext_bbox = draw.textbbox((0, 0), subtext, font=subtext_font)
    subtext_width = subtext_bbox[2] - subtext_bbox[0]
    subtext_height = subtext_bbox[3] - subtext_bbox[1]
    
    subtext_x = (img_width - subtext_width) // 2
    subtext_y = headline_y_start + (len(headline_lines) * (line_height + 15)) + 40
    
    # Draw subtext with stroke
    draw.text((subtext_x, subtext_y), subtext, font=subtext_font, fill=(220, 220, 220), 
              stroke_width=3, stroke_fill='black')
    
    # Draw sophisticated CTA banner
    banner_height = 110
    banner_y = img_height - banner_height
    
    # Convert hex color to RGB
    color_hex = brief.get('primary_color_hex', '#B71C1C')
    if color_hex.startswith('#'):
        color_hex = color_hex[1:]
    
    try:
        banner_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except:
        banner_color = (183, 28, 28)  # Default red
    
    # Draw banner with gradient effect
    for banner_y_pos in range(banner_y, img_height):
        intensity = int(50 * (1 - (banner_y_pos - banner_y) / banner_height))
        gradient_color = tuple(max(0, c - intensity) for c in banner_color)
        draw.rectangle([0, banner_y_pos, img_width, banner_y_pos + 1], fill=gradient_color)
    
    # Draw CTA text
    cta_text = random.choice(engagement_hooks)
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    cta_height = cta_bbox[3] - cta_bbox[1]
    
    cta_x = (img_width - cta_width) // 2
    cta_y = banner_y + (banner_height - cta_height) // 2
    
    # Draw CTA text with sophisticated stroke
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill='white', 
              stroke_width=3, stroke_fill='black')
    
    return final_image


def generate_hashtags(hashtag_categories):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(hashtag_categories['viral'], 2))
    hashtags.extend(random.sample(hashtag_categories['controversial'], 2))
    hashtags.extend(random.sample(hashtag_categories['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Advanced AI Director System"""
    
    print("The Unseen Economy - Advanced AI Director System")
    print("=" * 60)
    
    # Setup
    constants = setup()
    gemini_model = constants['gemini_model']
    
    try:
        # Step 1: Advanced AI Art Director generates creative brief
        print("Advanced AI Art Director generating sophisticated creative brief...")
        brief = get_creative_brief(gemini_model)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Style: {brief['style_description']}")
        print(f"Visual Concept: {brief.get('visual_concept', 'N/A')}")
        print(f"Color: {brief['primary_color_hex']}")
        
        # Step 2: Create sophisticated background
        print("Creating sophisticated AI-inspired background...")
        base_image = create_sophisticated_background(brief)
        
        # Step 3: Create professional post
        print("Creating professional post with perfect text overlay...")
        final_image = create_professional_post(base_image, brief, constants['engagement_hooks'])
        
        # Step 4: Save final image
        final_image.save('advanced_ai_post.png')
        print("Successfully generated advanced_ai_post.png")
        
        # Step 5: Generate hashtags
        hashtags = generate_hashtags(constants['hashtag_categories'])
        
        # Print summary
        print("\n" + "="*60)
        print("ADVANCED AI DIRECTOR SYSTEM OUTPUT:")
        print("="*60)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Style: {brief['style_description']}")
        print(f"Visual Concept: {brief.get('visual_concept', 'N/A')}")
        print(f"CTA Color: {brief['primary_color_hex']}")
        print(f"Hashtags: {hashtags}")
        print("="*60)
        
        # Save creative brief
        with open('advanced_creative_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        print("Advanced creative brief saved to advanced_creative_brief.json")
        
    except Exception as e:
        print(f"Error in Advanced AI Director system: {e}")
        return


if __name__ == "__main__":
    main()




