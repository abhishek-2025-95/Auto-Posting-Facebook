#!/usr/bin/env python3
"""
The Unseen Economy - Professional Demo Pipeline
Shows the complete workflow without requiring OpenAI API key
"""

import os
import random
import json
from PIL import Image, ImageDraw, ImageFont


def setup():
    """Initialize all constants"""
    
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
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'img_width': IMG_WIDTH,
        'img_height': IMG_HEIGHT
    }


def generate_viral_take():
    """Generate a viral economic take (demo version)"""
    
    # Pre-written viral takes
    viral_takes = [
        {
            'headline': 'The gig economy isn\'t the future of work',
            'subtext': '- it\'s the return of medieval serfdom with better marketing.'
        },
        {
            'headline': 'The top 1% captured 82% of all new wealth',
            'subtext': '- while the bottom 50% saw zero increase.'
        },
        {
            'headline': 'The average CEO makes 350x more than workers',
            'subtext': '- in 1965, it was 20x. This isn\'t meritocracy.'
        },
        {
            'headline': 'The \'free market\' is a myth',
            'subtext': '- 5 companies control 90% of what you consume.'
        },
        {
            'headline': 'The American Dream is now a subscription service',
            'subtext': '- everything became a monthly payment.'
        },
        {
            'headline': 'The top 1% own more wealth than the bottom 90%',
            'subtext': '- this isn\'t capitalism, it\'s feudalism with technology.'
        },
        {
            'headline': 'The average American has $90,000 in debt',
            'subtext': '- but only $8,000 in savings. This isn\'t personal failure.'
        },
        {
            'headline': 'The minimum wage should be $25/hour',
            'subtext': '- not $15. Here\'s the math that will explode your head.'
        }
    ]
    
    return random.choice(viral_takes)


def generate_image_prompt(theme_description):
    """Generate DALL-E 3 prompt for background image (demo version)"""
    
    # Pre-written professional image prompts
    image_prompts = [
        "A dark, neo-brutalist composition with stark geometric shapes and high contrast. Abstract representation of economic inequality with dramatic shadows and cinematic lighting. Professional, minimalist, text-free background.",
        "A surreal, hyper-realistic depiction of a massive golden hand reaching down from a stormy sky, plucking wealth from a barren landscape where tiny figures struggle. Gothic cyberpunk style with dramatic lighting and high contrast.",
        "An abstract, minimalist infographic showing a single massive bar towering over tiny bars, representing wealth inequality. Clean lines, stark contrast, professional data visualization style, text-free.",
        "A dystopian cityscape with towering corporate buildings casting shadows over a neighborhood of small houses. Dark, cinematic lighting with neon accents. Professional, text-free background.",
        "A dramatic, high-contrast composition showing a scale with a massive golden weight on one side and tiny weights on the other. Neo-brutalist style with stark shadows and professional lighting.",
        "An abstract representation of economic systems as a complex network of glowing lines and nodes, with one massive central hub dominating smaller connections. High-tech data art style, text-free.",
        "A surreal scene of a person trapped inside a transparent cube made of money, while outside a crowd reaches toward them. Hyper-realistic with dramatic lighting and emotional impact.",
        "A minimalist composition showing a single percentage symbol (1%) carved into a concrete wall, with a tiny percentage (99%) barely visible in the corner. Raw, industrial textures with high contrast."
    ]
    
    return random.choice(image_prompts)


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
    """Main orchestrator function (demo version)"""
    
    print("The Unseen Economy - Professional Demo Pipeline")
    print("=" * 60)
    
    # Setup
    constants = setup()
    
    try:
        # Step 1: Generate viral take
        print("Generating viral take...")
        take = generate_viral_take()
        print(f"Headline: {take['headline']}")
        print(f"Subtext: {take['subtext']}")
        
        # Step 2: Generate image prompt
        print("Creating image prompt...")
        theme = take['headline'] + ' ' + take['subtext']
        img_prompt = generate_image_prompt(theme)
        print(f"Image prompt: {img_prompt[:100]}...")
        
        # Step 3: Create demo background
        print("Creating demo background...")
        base_img = create_demo_background()
        
        # Step 4: Create professional post
        print("Creating professional post...")
        cta = random.choice(constants['engagement_hooks'])
        final_image = create_professional_post(base_img, take['headline'], take['subtext'], cta)
        
        # Step 5: Save final image
        final_image.save('final_post.png')
        print("Successfully generated final_post.png")
        
        # Step 6: Generate hashtags
        hashtags = generate_hashtags(constants)
        
        # Print content for Facebook post
        print("\n" + "="*60)
        print("CONTENT FOR FACEBOOK POST:")
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
            'image_prompt': img_prompt
        }
        
        with open('content_data.json', 'w') as f:
            json.dump(content_data, f, indent=2)
        
        print("Content data saved to content_data.json")
        
    except Exception as e:
        print(f"Error in main pipeline: {e}")
        return


if __name__ == "__main__":
    main()




