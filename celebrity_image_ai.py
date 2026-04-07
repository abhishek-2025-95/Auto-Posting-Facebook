#!/usr/bin/env python3
"""
The Unseen Economy - Celebrity Image AI System
Generates viral celebrity news with AI-generated celebrity images
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
visual_concept: A detailed description of the symbolic background design
background_elements: Specific visual elements to include
color_palette: Main colors for the background
mood_keywords: 3-5 words describing the emotional tone
primary_color_hex: Hex color for CTA banner

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
            "visual_concept": "A massive celebrity mansion with hidden offshore accounts and tax documents scattered around",
            "background_elements": ["mansion", "offshore accounts", "tax documents", "money bags"],
            "color_palette": ["#1a1a1a", "#2d2d2d", "#ff4444", "#ffffff"],
            "mood_keywords": ["outrage", "unfair", "corrupt", "scandalous"],
            "primary_color_hex": "#FF4444"
        }


def generate_celebrity_image_prompt(brief):
    """
    Generate a prompt for creating a celebrity image using AI
    """
    
    celebrity = brief.get('celebrity', 'Celebrity')
    celebrity_description = brief.get('celebrity_description', 'A celebrity')
    scandal_type = brief.get('scandal_type', 'Scandal')
    
    # Create a detailed prompt for celebrity image generation
    image_prompt = f"""Professional headshot of {celebrity}, {celebrity_description}. 
    
    The image should show:
    - A confident, smug expression
    - Professional business attire
    - High-end, luxurious setting
    - Dramatic lighting
    - Corporate boardroom or luxury office background
    - Subtle signs of wealth and power
    
    Style: Professional corporate photography, high-end, dramatic lighting, 
    photorealistic, high resolution, corporate headshot style.
    
    The celebrity should look powerful, wealthy, and slightly arrogant.
    Background should be luxurious and corporate.
    
    No text in the image."""
    
    return image_prompt


def create_celebrity_scandal_background(brief):
    """
    Create a sophisticated background based on the celebrity scandal
    """
    
    # Create base image
    img = Image.new('RGBA', (1024, 1024), color=(15, 15, 15, 255))  # Very dark base
    draw = ImageDraw.Draw(img)
    
    # Extract design elements from brief
    celebrity = brief.get('celebrity', 'Celebrity')
    scandal_type = brief.get('scandal_type', 'Scandal')
    visual_concept = brief.get('visual_concept', '')
    background_elements = brief.get('background_elements', [])
    color_palette = brief.get('color_palette', ['#1a1a1a', '#2d2d2d', '#ff4444', '#ffffff'])
    mood_keywords = brief.get('mood_keywords', ['outrage', 'unfair'])
    
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
        # Create complex gradient
        intensity = int(50 * (y / 1024))
        base_color = (15 + intensity, 15 + intensity, 15 + intensity, 255)
        draw.line([(0, y), (1024, y)], fill=base_color)
    
    # Create scandal-specific background
    if 'tax' in scandal_type.lower() or 'evasion' in scandal_type.lower():
        create_tax_evasion_visualization(draw, colors, celebrity)
    elif 'fraud' in scandal_type.lower() or 'greed' in scandal_type.lower():
        create_fraud_visualization(draw, colors, celebrity)
    elif 'offshore' in visual_concept.lower() or 'hidden' in visual_concept.lower():
        create_offshore_visualization(draw, colors, celebrity)
    elif 'mansion' in visual_concept.lower() or 'luxury' in visual_concept.lower():
        create_luxury_scandal_visualization(draw, colors, celebrity)
    else:
        create_generic_scandal_visualization(draw, colors, celebrity)
    
    # Add sophisticated texture overlay
    add_scandal_texture(draw, mood_keywords)
    
    return img


def create_tax_evasion_visualization(draw, colors, celebrity):
    """Create tax evasion visualization"""
    
    # Create celebrity mansion
    mansion_x = 200
    mansion_y = 1024 - 400
    mansion_width = 300
    mansion_height = 400
    
    # Mansion base
    draw.rectangle([mansion_x, mansion_y, mansion_x + mansion_width, 1024], fill=(80, 80, 80, 255))
    
    # Mansion windows (glowing)
    for window_y in range(mansion_y + 50, 1024 - 50, 60):
        for window_x in range(mansion_x + 30, mansion_x + mansion_width - 30, 40):
            if (window_x + window_y) % 80 < 40:
                draw.rectangle([window_x, window_y, window_x + 30, window_y + 40], fill=(255, 255, 150, 255))
    
    # Tax documents scattered around
    for i in range(8):
        doc_x = 600 + (i % 4) * 80
        doc_y = 1024 - 200 - (i // 4) * 100
        draw.rectangle([doc_x, doc_y, doc_x + 60, doc_y + 80], fill=(255, 255, 255, 200))
        # Add text lines on documents
        for line in range(3):
            draw.line([(doc_x + 10, doc_y + 20 + line * 15), (doc_x + 50, doc_y + 20 + line * 15)], fill=(0, 0, 0, 255), width=2)
    
    # Money bags
    for i in range(5):
        bag_x = 100 + i * 150
        bag_y = 1024 - 150
        draw.ellipse([bag_x, bag_y, bag_x + 80, bag_y + 100], fill=(255, 215, 0, 255))
        draw.text((bag_x + 20, bag_y + 30), "$", font=ImageFont.load_default(), fill=(0, 0, 0, 255))


def create_fraud_visualization(draw, colors, celebrity):
    """Create fraud visualization"""
    
    # Create corporate office building
    office_x = 300
    office_y = 1024 - 500
    office_width = 200
    office_height = 500
    
    # Office building
    draw.rectangle([office_x, office_y, office_x + office_width, 1024], fill=(60, 60, 60, 255))
    
    # Office windows
    for window_y in range(office_y + 30, 1024 - 30, 40):
        for window_x in range(office_x + 20, office_x + office_width - 20, 30):
            if (window_x + window_y) % 60 < 30:
                draw.rectangle([window_x, window_y, window_x + 25, window_y + 30], fill=(255, 255, 100, 255))
    
    # Fraud documents
    for i in range(6):
        doc_x = 600 + (i % 3) * 100
        doc_y = 1024 - 300 - (i // 3) * 150
        draw.rectangle([doc_x, doc_y, doc_x + 80, doc_y + 100], fill=(255, 255, 255, 200))
        # Add fraud symbols
        draw.text((doc_x + 30, doc_y + 40), "X", font=ImageFont.load_default(), fill=(255, 0, 0, 255))
    
    # Money flow arrows
    for i in range(3):
        start_x = office_x + office_width
        start_y = office_y + 100 + i * 100
        end_x = 600 + i * 100
        end_y = 1024 - 200
        draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 100, 100, 200), width=4)


def create_offshore_visualization(draw, colors, celebrity):
    """Create offshore accounts visualization"""
    
    # Create main landmass
    land_x = 100
    land_y = 1024 - 300
    land_width = 400
    land_height = 300
    
    draw.rectangle([land_x, land_y, land_x + land_width, 1024], fill=(40, 40, 40, 255))
    
    # Create offshore islands
    offshore_islands = [
        (600, 1024 - 200, 100, 200),
        (750, 1024 - 150, 80, 150),
        (900, 1024 - 180, 90, 180)
    ]
    
    for island_x, island_y, island_width, island_height in offshore_islands:
        draw.rectangle([island_x, island_y, island_x + island_width, 1024], fill=(60, 60, 60, 255))
    
    # Draw money flow lines from main land to offshore islands
    for island_x, island_y, island_width, island_height in offshore_islands:
        start_x = land_x + land_width
        start_y = land_y + 100
        end_x = island_x
        end_y = island_y + island_height // 2
        
        # Draw money flow
        for i in range(3):
            offset = i - 1
            draw.line([(start_x + offset, start_y), (end_x + offset, end_y)], fill=(255, 215, 0, 200), width=3)
    
    # Add money symbols on offshore islands
    for island_x, island_y, island_width, island_height in offshore_islands:
        draw.text((island_x + 20, island_y + 50), "$", font=ImageFont.load_default(), fill=(255, 215, 0, 255))


def create_luxury_scandal_visualization(draw, colors, celebrity):
    """Create luxury scandal visualization"""
    
    # Create luxury mansion
    mansion_x = 200
    mansion_y = 1024 - 500
    mansion_width = 400
    mansion_height = 500
    
    # Mansion base
    draw.rectangle([mansion_x, mansion_y, mansion_x + mansion_width, 1024], fill=(100, 100, 100, 255))
    
    # Mansion towers
    tower_heights = [600, 550, 500, 600, 550]
    for i, tower_height in enumerate(tower_heights):
        tower_x = mansion_x + (i * 80)
        tower_y = 1024 - tower_height
        draw.rectangle([tower_x, tower_y, tower_x + 60, 1024], fill=(120, 120, 120, 255))
    
    # Luxury cars
    for i in range(4):
        car_x = 700 + i * 80
        car_y = 1024 - 100
        draw.rectangle([car_x, car_y, car_x + 60, car_y + 40], fill=(255, 0, 0, 255))
    
    # Money piles
    for i in range(6):
        pile_x = 100 + i * 120
        pile_y = 1024 - 150
        draw.ellipse([pile_x, pile_y, pile_x + 80, pile_y + 100], fill=(255, 215, 0, 255))
        draw.text((pile_x + 30, pile_y + 40), "$", font=ImageFont.load_default(), fill=(0, 0, 0, 255))


def create_generic_scandal_visualization(draw, colors, celebrity):
    """Create generic scandal visualization"""
    
    # Create abstract scandal elements
    for i in range(5):
        center_x = 200 + i * 150
        center_y = 300 + i * 100
        size = 80 + i * 20
        
        # Create abstract scandal shapes
        draw.ellipse([center_x - size, center_y - size, center_x + size, center_y + size], 
                     fill=(100, 100, 100, 150))
    
    # Add scandal connections
    for i in range(8):
        start_x = 100 + i * 100
        start_y = 200
        end_x = 200 + i * 100
        end_y = 800
        
        # Draw scandal lines
        draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 100, 100, 150), width=4)
    
    # Add money symbols
    for i in range(10):
        x = random.randint(0, 1024)
        y = random.randint(0, 1024)
        draw.text((x, y), "$", font=ImageFont.load_default(), fill=(255, 215, 0, 255))


def add_scandal_texture(draw, mood_keywords):
    """Add scandal-specific texture"""
    
    if 'outrage' in mood_keywords:
        # Add outrage texture
        for i in range(0, 1024, 25):
            for j in range(0, 1024, 25):
                if (i + j) % 50 < 25:
                    alpha = random.randint(30, 70)
                    draw.rectangle([i, j, i + 12, j + 12], fill=(255, 100, 100, alpha))
    
    elif 'corrupt' in mood_keywords:
        # Add corruption texture
        for i in range(0, 1024, 35):
            for j in range(0, 1024, 35):
                if (i + j) % 70 < 35:
                    alpha = random.randint(20, 60)
                    draw.rectangle([i, j, i + 18, j + 18], fill=(0, 0, 0, alpha))
    
    else:
        # Add subtle scandal texture
        for i in range(0, 1024, 40):
            for j in range(0, 1024, 40):
                if (i + j) % 80 < 40:
                    alpha = random.randint(10, 40)
                    draw.rectangle([i, j, i + 20, j + 20], fill=(255, 255, 255, alpha))


def create_celebrity_placeholder():
    """
    Create a placeholder celebrity image since we can't generate real celebrity images
    """
    
    # Create a placeholder celebrity image
    img = Image.new('RGBA', (300, 400), color=(50, 50, 50, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple celebrity silhouette
    # Head
    draw.ellipse([100, 50, 200, 150], fill=(200, 180, 160, 255))
    
    # Body (suit)
    draw.rectangle([80, 150, 220, 350], fill=(100, 100, 100, 255))
    
    # Tie
    draw.rectangle([140, 150, 160, 250], fill=(200, 0, 0, 255))
    
    # Arms
    draw.rectangle([60, 180, 80, 280], fill=(200, 180, 160, 255))
    draw.rectangle([220, 180, 240, 280], fill=(200, 180, 160, 255))
    
    # Add some luxury elements
    # Watch
    draw.ellipse([70, 200, 90, 220], fill=(255, 215, 0, 255))
    
    # Ring
    draw.ellipse([190, 220, 210, 240], fill=(255, 215, 0, 255))
    
    return img


def create_professional_post_with_celebrity(base_image, brief, engagement_hooks):
    """
    Create professional post with celebrity image overlay
    """
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Add sophisticated scrim overlay
    overlay = Image.new('RGBA', final_image.size, (0, 0, 0, 100))
    final_image = Image.alpha_composite(final_image, overlay)
    draw = ImageDraw.Draw(final_image)
    
    # Create celebrity placeholder
    celebrity_img = create_celebrity_placeholder()
    
    # Resize celebrity image
    celebrity_img = celebrity_img.resize((200, 250))
    
    # Paste celebrity image on the right side
    celebrity_x = 1024 - 220  # Right side with margin
    celebrity_y = 200  # Upper area
    
    # Create a frame for the celebrity image
    frame_color = (255, 215, 0, 255)  # Gold frame
    draw.rectangle([celebrity_x - 5, celebrity_y - 5, celebrity_x + 205, celebrity_y + 255], 
                   fill=frame_color, width=3)
    
    # Paste celebrity image
    final_image.paste(celebrity_img, (celebrity_x, celebrity_y), celebrity_img)
    
    # Load fonts
    try:
        headline_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 75)
        subtext_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 38)
        cta_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
    except:
        try:
            headline_font = ImageFont.truetype("arial.ttf", 75)
            subtext_font = ImageFont.truetype("arial.ttf", 38)
            cta_font = ImageFont.truetype("arial.ttf", 36)
        except:
            headline_font = ImageFont.load_default()
            subtext_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
    
    # Get image dimensions
    img_width, img_height = final_image.size
    
    # Draw headline with perfect text wrapping (left side to avoid celebrity)
    headline = brief['headline']
    subtext = brief['subtext']
    
    # Wrap headline text to prevent overflow
    headline_lines = textwrap.wrap(headline, width=16)
    if len(headline_lines) > 2:
        headline_lines = headline_lines[:2]
    
    # Calculate headline position (left side)
    headline_y_start = img_height // 2 - 120
    headline_x_start = 50  # Left side
    
    for i, line in enumerate(headline_lines):
        line_bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        line_x = headline_x_start
        line_y = headline_y_start + (i * (line_height + 15))
        
        # Draw headline with sophisticated stroke
        draw.text((line_x, line_y), line, font=headline_font, fill='white', 
                  stroke_width=4, stroke_fill='black')
    
    # Draw subtext with perfect positioning (left side)
    subtext_bbox = draw.textbbox((0, 0), subtext, font=subtext_font)
    subtext_width = subtext_bbox[2] - subtext_bbox[0]
    subtext_height = subtext_bbox[3] - subtext_bbox[1]
    
    subtext_x = headline_x_start
    subtext_y = headline_y_start + (len(headline_lines) * (line_height + 15)) + 40
    
    # Draw subtext with stroke
    draw.text((subtext_x, subtext_y), subtext, font=subtext_font, fill=(230, 230, 230), 
              stroke_width=3, stroke_fill='black')
    
    # Draw sophisticated CTA banner
    banner_height = 110
    banner_y = img_height - banner_height
    
    # Convert hex color to RGB
    color_hex = brief.get('primary_color_hex', '#FF4444')
    if color_hex.startswith('#'):
        color_hex = color_hex[1:]
    
    try:
        banner_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except:
        banner_color = (255, 68, 68)  # Default red
    
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
    """Celebrity Image AI System"""
    
    print("The Unseen Economy - Celebrity Image AI System")
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
        
        # Step 2: Create scandal background
        print("Creating celebrity scandal background...")
        base_image = create_celebrity_scandal_background(brief)
        
        # Step 3: Create professional post with celebrity
        print("Creating professional post with celebrity image...")
        final_image = create_professional_post_with_celebrity(base_image, brief, constants['engagement_hooks'])
        
        # Step 4: Save final image
        final_image.save('celebrity_image_post.png')
        print("Successfully generated celebrity_image_post.png")
        
        # Step 5: Generate hashtags
        hashtags = generate_hashtags(constants['hashtag_categories'])
        
        # Print summary
        print("\n" + "="*60)
        print("CELEBRITY IMAGE AI SYSTEM OUTPUT:")
        print("="*60)
        print(f"Headline: {brief['headline']}")
        print(f"Subtext: {brief['subtext']}")
        print(f"Celebrity: {brief['celebrity']}")
        print(f"Scandal: {brief['scandal_type']}")
        print(f"Story: {brief['story_summary']}")
        print(f"CTA Color: {brief['primary_color_hex']}")
        print(f"Hashtags: {hashtags}")
        print("="*60)
        
        # Save creative brief
        with open('celebrity_image_brief.json', 'w') as f:
            json.dump(brief, f, indent=2)
        
        print("Celebrity image brief saved to celebrity_image_brief.json")
        
    except Exception as e:
        print(f"Error in Celebrity Image AI system: {e}")
        return


if __name__ == "__main__":
    main()




