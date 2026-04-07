#!/usr/bin/env python3
"""
The Unseen Economy - Truly Sophisticated AI System
Creates genuinely unique, sophisticated backgrounds based on AI creative briefs
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
    Get a truly unique creative brief from Gemini AI
    """
    
    system_prompt = """You are an elite AI Art Director for 'The Unseen Economy.' Create a unique, sophisticated creative brief in JSON format.

Your output MUST be a JSON object with these exact keys:

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

    user_prompt = "Generate a completely new, unique creative brief for a viral economic justice post."
    
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
        # Return unique fallback
        return {
            "headline": "They own your future. You rent it.",
            "subtext": "Every paycheck is a tribute to the new feudal lords.",
            "theme": "Digital Feudalism",
            "style_description": "A dystopian cyberpunk aesthetic with neon-lit corporate towers casting shadows over digital serfs",
            "primary_color_hex": "#FF6B35",
            "visual_concept": "A massive, glowing corporate headquarters with digital chains extending to smaller buildings below",
            "background_elements": ["neon lights", "digital chains", "corporate towers", "oppressive shadows"],
            "color_palette": ["#0a0a0a", "#1a1a1a", "#ff6b35", "#00ff88"],
            "mood_keywords": ["dystopian", "oppressive", "digital", "corporate", "unjust"]
        }


def create_truly_unique_background(brief):
    """
    Create a truly unique, sophisticated background based on the creative brief
    """
    
    # Create base image
    img = Image.new('RGBA', (1024, 1024), color=(10, 10, 10, 255))  # Very dark base
    draw = ImageDraw.Draw(img)
    
    # Extract design elements from brief
    theme = brief.get('theme', '').lower()
    visual_concept = brief.get('visual_concept', '')
    background_elements = brief.get('background_elements', [])
    color_palette = brief.get('color_palette', ['#0a0a0a', '#1a1a1a', '#ff6b35', '#00ff88'])
    mood_keywords = brief.get('mood_keywords', ['dystopian', 'oppressive'])
    
    # Convert hex colors to RGB
    colors = []
    for color_hex in color_palette:
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        try:
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            colors.append(rgb)
        except:
            colors.append((255, 107, 53, 255))  # Default orange
    
    # Create sophisticated gradient background
    for y in range(1024):
        # Create complex gradient
        intensity = int(40 * (y / 1024))
        base_color = (10 + intensity, 10 + intensity, 10 + intensity, 255)
        draw.line([(0, y), (1024, y)], fill=base_color)
    
    # Create unique background based on visual concept
    if 'corporate' in visual_concept.lower() or 'tower' in visual_concept.lower():
        create_corporate_tower_visualization(draw, colors, visual_concept)
    elif 'chain' in visual_concept.lower() or 'control' in visual_concept.lower():
        create_control_chain_visualization(draw, colors, visual_concept)
    elif 'feudalism' in theme.lower() or 'feudal' in theme.lower():
        create_feudal_system_visualization(draw, colors, visual_concept)
    elif 'wealth' in theme.lower() or 'inequality' in theme.lower():
        create_wealth_pyramid_visualization(draw, colors, visual_concept)
    else:
        create_abstract_oppression_visualization(draw, colors, visual_concept)
    
    # Add sophisticated texture overlay
    add_unique_texture(draw, mood_keywords)
    
    return img


def create_corporate_tower_visualization(draw, colors, visual_concept):
    """Create sophisticated corporate tower visualization"""
    
    # Create massive corporate headquarters
    tower_width = 120
    tower_height = 800
    tower_x = 400
    tower_y = 1024 - tower_height
    
    # Main tower with gradient
    for y in range(tower_y, 1024):
        intensity = int(60 * (1 - (y - tower_y) / tower_height))
        tower_color = (20 + intensity, 20 + intensity, 20 + intensity, 255)
        draw.rectangle([tower_x, y, tower_x + tower_width, y + 1], fill=tower_color)
    
    # Add glowing windows
    for window_y in range(tower_y + 50, 1024 - 50, 60):
        for window_x in range(tower_x + 20, tower_x + tower_width - 20, 30):
            if (window_x + window_y) % 80 < 40:  # Sophisticated pattern
                draw.rectangle([window_x, window_y, window_x + 25, window_y + 40], fill=(255, 255, 150, 255))
    
    # Add power lines extending to smaller buildings
    smaller_buildings = [
        (150, 1024 - 200, 80, 200),
        (700, 1024 - 300, 100, 300),
        (900, 1024 - 150, 60, 150)
    ]
    
    for building_x, building_y, building_width, building_height in smaller_buildings:
        # Draw smaller building
        draw.rectangle([building_x, building_y, building_x + building_width, 1024], fill=(40, 40, 40, 255))
        
        # Draw power line from main tower
        line_start_x = tower_x + tower_width
        line_start_y = tower_y + 200
        line_end_x = building_x
        line_end_y = building_y + building_height // 2
        
        # Draw glowing power line
        for i in range(5):
            offset = i - 2
            draw.line([(line_start_x + offset, line_start_y), (line_end_x + offset, line_end_y)], 
                     fill=(255, 100, 100, 150), width=3)
    
    # Add atmospheric effects
    for i in range(20):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        size = random.randint(2, 8)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255, 30))


def create_control_chain_visualization(draw, colors, visual_concept):
    """Create sophisticated control chain visualization"""
    
    # Create central control hub
    hub_x = 512
    hub_y = 200
    hub_size = 80
    
    # Control hub
    draw.ellipse([hub_x - hub_size, hub_y - hub_size, hub_x + hub_size, hub_y + hub_size], 
                 fill=(255, 100, 100, 255))
    
    # Create digital chains to controlled entities
    controlled_entities = [
        (200, 600, 60, 150),
        (400, 700, 80, 120),
        (600, 650, 70, 140),
        (800, 580, 90, 160)
    ]
    
    for entity_x, entity_y, entity_width, entity_height in controlled_entities:
        # Draw controlled entity
        draw.rectangle([entity_x, entity_y, entity_x + entity_width, 1024], fill=(60, 60, 60, 255))
        
        # Draw digital chain
        chain_points = []
        for i in range(10):
            t = i / 9
            x = int(hub_x + (entity_x - hub_x) * t)
            y = int(hub_y + (entity_y - hub_y) * t)
            chain_points.append((x, y))
        
        # Draw chain segments
        for i in range(len(chain_points) - 1):
            draw.line([chain_points[i], chain_points[i + 1]], fill=(255, 200, 100, 200), width=4)
    
    # Add digital effects
    for i in range(15):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        draw.rectangle([x, y, x + 2, y + 2], fill=(0, 255, 255, 100))


def create_feudal_system_visualization(draw, colors, visual_concept):
    """Create sophisticated feudal system visualization"""
    
    # Create castle/manor house
    castle_x = 300
    castle_y = 1024 - 500
    castle_width = 200
    castle_height = 500
    
    # Castle base
    draw.rectangle([castle_x, castle_y, castle_x + castle_width, 1024], fill=(80, 80, 80, 255))
    
    # Castle towers
    tower_heights = [600, 550, 500, 600]
    for i, tower_height in enumerate(tower_heights):
        tower_x = castle_x + (i * 50)
        tower_y = 1024 - tower_height
        draw.rectangle([tower_x, tower_y, tower_x + 40, 1024], fill=(100, 100, 100, 255))
    
    # Serf dwellings (small, scattered)
    serf_dwellings = [
        (600, 1024 - 120, 50, 120),
        (700, 1024 - 100, 40, 100),
        (800, 1024 - 140, 45, 140),
        (900, 1024 - 110, 55, 110)
    ]
    
    for dwelling_x, dwelling_y, dwelling_width, dwelling_height in serf_dwellings:
        draw.rectangle([dwelling_x, dwelling_y, dwelling_x + dwelling_width, 1024], fill=(40, 40, 40, 255))
    
    # Add feudal connections
    for dwelling_x, dwelling_y, dwelling_width, dwelling_height in serf_dwellings:
        line_start_x = castle_x + 100
        line_start_y = 1024 - 200
        line_end_x = dwelling_x + dwelling_width // 2
        line_end_y = dwelling_y + dwelling_height // 2
        
        draw.line([(line_start_x, line_start_y), (line_end_x, line_end_y)], 
                 fill=(255, 150, 150, 150), width=3)


def create_wealth_pyramid_visualization(draw, colors, visual_concept):
    """Create sophisticated wealth pyramid visualization"""
    
    # Create wealth pyramid
    pyramid_base = 800
    pyramid_height = 600
    pyramid_x = 112  # (1024 - pyramid_base) // 2
    pyramid_y = 1024 - pyramid_height
    
    # Draw pyramid levels
    levels = [200, 150, 100, 50, 20]
    level_heights = [120, 120, 120, 120, 120]
    
    current_y = pyramid_y
    for i, (level_width, level_height) in enumerate(zip(levels, level_heights)):
        level_x = (1024 - level_width) // 2
        
        # Color based on wealth level
        if i < 2:  # Top levels
            level_color = (255, 100, 100, 255)  # Red for extreme wealth
        elif i < 3:  # Middle level
            level_color = (255, 200, 100, 255)  # Orange for high wealth
        else:  # Bottom levels
            level_color = (100, 100, 100, 255)  # Gray for low wealth
        
        draw.rectangle([level_x, current_y, level_x + level_width, current_y + level_height], 
                      fill=level_color)
        current_y += level_height
    
    # Add wealth distribution bars
    bar_width = 15
    bar_spacing = 20
    start_x = 50
    start_y = 1024 - 100
    
    bars = [20, 35, 60, 120, 250, 400]
    
    for i, bar_height in enumerate(bars):
        x = start_x + (i * (bar_width + bar_spacing))
        y = start_y - bar_height
        
        if bar_height > 200:
            color = (255, 68, 68, 255)
        elif bar_height > 100:
            color = (255, 170, 68, 255)
        else:
            color = (100, 100, 100, 255)
        
        draw.rectangle([x, y, x + bar_width, start_y], fill=color)


def create_abstract_oppression_visualization(draw, colors, visual_concept):
    """Create sophisticated abstract oppression visualization"""
    
    # Create abstract oppressive forms
    for i in range(5):
        center_x = 200 + i * 150
        center_y = 300 + i * 100
        size = 100 + i * 30
        
        # Create abstract oppressive shapes
        draw.ellipse([center_x - size, center_y - size, center_x + size, center_y + size], 
                     fill=(60, 60, 60, 150))
    
    # Add oppressive connections
    for i in range(8):
        start_x = 100 + i * 100
        start_y = 200
        end_x = 200 + i * 100
        end_y = 800
        
        # Draw oppressive lines
        draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 100, 100, 150), width=4)
    
    # Add atmospheric oppression
    for i in range(30):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        size = random.randint(3, 12)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 100, 100, 50))


def add_unique_texture(draw, mood_keywords):
    """Add unique texture based on mood"""
    
    if 'dystopian' in mood_keywords:
        # Add dystopian texture
        for i in range(0, 1024, 30):
            for j in range(0, 1024, 30):
                if (i + j) % 60 < 30:
                    alpha = random.randint(20, 60)
                    draw.rectangle([i, j, i + 15, j + 15], fill=(255, 100, 100, alpha))
    
    elif 'oppressive' in mood_keywords:
        # Add oppressive texture
        for i in range(0, 1024, 40):
            for j in range(0, 1024, 40):
                if (i + j) % 80 < 40:
                    alpha = random.randint(10, 40)
                    draw.rectangle([i, j, i + 20, j + 20], fill=(0, 0, 0, alpha))
    
    else:
        # Add subtle texture
        for i in range(0, 1024, 50):
            for j in range(0, 1024, 50):
                if (i + j) % 100 < 50:
                    alpha = random.randint(5, 25)
                    draw.rectangle([i, j, i + 25, j + 25], fill=(255, 255, 255, alpha))


def create_professional_post(base_image, brief, engagement_hooks):
    """
    Create professional post with perfect text overlay
    """
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Add sophisticated scrim overlay
    overlay = Image.new('RGBA', final_image.size, (0, 0, 0, 120))
    final_image = Image.alpha_composite(final_image, overlay)
    draw = ImageDraw.Draw(final_image)
    
    # Load fonts
    try:
        headline_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 90)
        subtext_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 45)
        cta_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
    except:
        try:
            headline_font = ImageFont.truetype("arial.ttf", 90)
            subtext_font = ImageFont.truetype("arial.ttf", 45)
            cta_font = ImageFont.truetype("arial.ttf", 40)
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
    headline_lines = textwrap.wrap(headline, width=16)
    if len(headline_lines) > 2:
        headline_lines = headline_lines[:2]
    
    # Calculate headline position
    headline_y_start = img_height // 2 - 140
    
    for i, line in enumerate(headline_lines):
        line_bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        line_x = (img_width - line_width) // 2
        line_y = headline_y_start + (i * (line_height + 20))
        
        # Draw headline with sophisticated stroke
        draw.text((line_x, line_y), line, font=headline_font, fill='white', 
                  stroke_width=5, stroke_fill='black')
    
    # Draw subtext with perfect positioning
    subtext_bbox = draw.textbbox((0, 0), subtext, font=subtext_font)
    subtext_width = subtext_bbox[2] - subtext_bbox[0]
    subtext_height = subtext_bbox[3] - subtext_bbox[1]
    
    subtext_x = (img_width - subtext_width) // 2
    subtext_y = headline_y_start + (len(headline_lines) * (line_height + 20)) + 50
    
    # Draw subtext with stroke
    draw.text((subtext_x, subtext_y), subtext, font=subtext_font, fill=(230, 230, 230), 
              stroke_width=4, stroke_fill='black')
    
    # Draw sophisticated CTA banner
    banner_height = 120
    banner_y = img_height - banner_height
    
    # Convert hex color to RGB
    color_hex = brief.get('primary_color_hex', '#FF6B35')
    if color_hex.startswith('#'):
        color_hex = color_hex[1:]
    
    try:
        banner_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except:
        banner_color = (255, 107, 53)  # Default orange
    
    # Draw banner with gradient effect
    for banner_y_pos in range(banner_y, img_height):
        intensity = int(60 * (1 - (banner_y_pos - banner_y) / banner_height))
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
              stroke_width=4, stroke_fill='black')
    
    return final_image


def generate_hashtags(hashtag_categories):
    """Generate hashtags for Facebook post"""
    
    hashtags = []
    hashtags.extend(random.sample(hashtag_categories['viral'], 2))
    hashtags.extend(random.sample(hashtag_categories['controversial'], 2))
    hashtags.extend(random.sample(hashtag_categories['problem_focused'], 2))
    
    return ' '.join(hashtags)


def main():
    """Truly Sophisticated AI System"""
    
    print("The Unseen Economy - Truly Sophisticated AI System")
    print("=" * 60)
    
    # Setup
    constants = setup()
    gemini_model = constants['gemini_model']
    
    try:
        # Step 1: Get unique creative brief
        print("Generating truly unique creative brief...")
        brief = get_creative_brief(gemini_model)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Visual Concept: {brief.get('visual_concept', 'N/A')}")
        print(f"Color: {brief['primary_color_hex']}")
        
        # Step 2: Create truly unique background
        print("Creating truly unique, sophisticated background...")
        base_image = create_truly_unique_background(brief)
        
        # Step 3: Create professional post
        print("Creating professional post with perfect text overlay...")
        final_image = create_professional_post(base_image, brief, constants['engagement_hooks'])
        
        # Step 4: Save final image
        final_image.save('truly_sophisticated_post.png')
        print("Successfully generated truly_sophisticated_post.png")
        
        # Step 5: Generate hashtags
        hashtags = generate_hashtags(constants['hashtag_categories'])
        
        # Print summary
        print("\n" + "="*60)
        print("TRULY SOPHISTICATED AI SYSTEM OUTPUT:")
        print("="*60)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Theme: {brief['theme']}")
        print(f"Visual Concept: {brief.get('visual_concept', 'N/A')}")
        print(f"CTA Color: {brief['primary_color_hex']}")
        print(f"Hashtags: {hashtags}")
        print("="*60)
        
        # Save creative brief
        with open('truly_sophisticated_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        print("Truly sophisticated creative brief saved to truly_sophisticated_brief.json")
        
    except Exception as e:
        print(f"Error in Truly Sophisticated AI system: {e}")
        return


if __name__ == "__main__":
    main()




