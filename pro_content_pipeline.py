#!/usr/bin/env python3
"""
The Unseen Economy - Professional Content Pipeline
Generates viral-ready image posts with DALL-E 3 backgrounds + professional text overlay
"""

import os
import random
import json
import requests
import io
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI


def setup():
    """Initialize all constants and OpenAI client"""
    
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
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'img_width': IMG_WIDTH,
        'img_height': IMG_HEIGHT,
        'client': client
    }


def generate_viral_take(client):
    """Generate a viral economic take using ChatCompletion API"""
    
    system_prompt = """You generate content for 'The Unseen Economy' page. Create a viral economic take as a JSON object with two keys: headline (the main shocking statement) and subtext (the 'medieval serfdom' style punchline). Target: US/EU Millennials on economic inequality.

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

Make it angry, provocative, and designed to go viral."""
    
    user_prompt = "Generate a new viral take for the 'gig economy' theme."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.9
        )
        
        # Parse JSON response
        content = response.choices[0].message.content.strip()
        take = json.loads(content)
        
        return take
    
    except Exception as e:
        print(f"Error generating viral take: {e}")
        # Fallback content
        return {
            'headline': 'The gig economy isn\'t the future of work',
            'subtext': '- it\'s the return of medieval serfdom with better marketing.'
        }


def generate_image_prompt(theme_description):
    """Generate DALL-E 3 prompt for background image"""
    
    system_prompt = """You are a creative director. Create a DALL-E 3 prompt for a background graphic or symbolic asset. This image will have text overlaid on it later. It must be abstract, minimalist, or symbolic, look professional, and be text-free. The style should be high-end: neo-brutalist, abstract data-art, or surreal photorealism. High contrast, dark, and cinematic.

The image should symbolically represent the economic theme without any text or numbers visible."""
    
    user_prompt = f"Create a background graphic for the theme: {theme_description}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        return "A dark, neo-brutalist composition with stark geometric shapes and high contrast. Abstract representation of economic inequality with dramatic shadows and cinematic lighting. Professional, minimalist, text-free background."


def generate_and_download_image(client, image_prompt):
    """Generate DALL-E 3 image and download it"""
    
    try:
        print(f"Generating DALL-E 3 image with prompt: {image_prompt[:100]}...")
        
        # Generate image with DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        image_url = response.data[0].url
        print(f"Image generated: {image_url}")
        
        # Download the image
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        
        # Open image with Pillow
        image = Image.open(io.BytesIO(img_response.content))
        
        # Ensure RGBA mode for compositing
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        print("Image downloaded and processed successfully")
        return image
    
    except Exception as e:
        print(f"Error generating/downloading image: {e}")
        # Create fallback image
        fallback = Image.new('RGBA', (1024, 1024), color=(20, 20, 20, 255))
        return fallback


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
    """Main orchestrator function"""
    
    print("The Unseen Economy - Professional Content Pipeline")
    print("=" * 60)
    
    # Setup
    constants = setup()
    client = constants['client']
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Step 1: Generate viral take
        print("Generating viral take...")
        take = generate_viral_take(client)
        print(f"Headline: {take['headline']}")
        print(f"Subtext: {take['subtext']}")
        
        # Step 2: Generate image prompt
        print("Creating image prompt...")
        theme = take['headline'] + ' ' + take['subtext']
        img_prompt = generate_image_prompt(theme)
        print(f"Image prompt: {img_prompt[:100]}...")
        
        # Step 3: Generate and download image
        print("Generating DALL-E 3 image...")
        base_img = generate_and_download_image(client, img_prompt)
        
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




