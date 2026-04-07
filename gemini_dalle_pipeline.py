#!/usr/bin/env python3
"""
The Unseen Economy - Gemini + DALL-E 3 Hybrid Pipeline
Uses Gemini AI for content generation and DALL-E 3 for professional images
"""

import os
import random
import json
import requests
import io
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from openai import OpenAI


def setup():
    """Initialize all constants and AI clients"""
    
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
    
    # Configure OpenAI (for DALL-E 3)
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'img_width': IMG_WIDTH,
        'img_height': IMG_HEIGHT,
        'gemini_model': genai.GenerativeModel('gemini-2.5-flash'),
        'openai_client': openai_client
    }


def generate_viral_take(gemini_model):
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
        response = gemini_model.generate_content(prompt)
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


def generate_image_prompt(theme_description, gemini_model):
    """Generate DALL-E 3 prompt for background image using Gemini"""
    
    prompt = f"""You are a creative director. Create a DALL-E 3 prompt for a background graphic or symbolic asset. This image will have text overlaid on it later. It must be abstract, minimalist, or symbolic, look professional, and be text-free. The style should be high-end: neo-brutalist, abstract data-art, or surreal photorealism. High contrast, dark, and cinematic.

The image should symbolically represent the economic theme: {theme_description}

Return ONLY the DALL-E 3 prompt text, no explanations."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        print(f"Error generating image prompt with Gemini: {e}")
        return "A dark, neo-brutalist composition with stark geometric shapes and high contrast. Abstract representation of economic inequality with dramatic shadows and cinematic lighting. Professional, minimalist, text-free background."


def generate_dalle_image(image_prompt, openai_client):
    """Generate and download DALL-E 3 image"""
    
    try:
        print("Generating DALL-E 3 image...")
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        image_url = response.data[0].url
        print(f"DALL-E 3 image generated: {image_url}")
        
        # Download the image
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        
        # Open with Pillow
        image = Image.open(io.BytesIO(img_response.content))
        
        # Convert to RGBA for compositing
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        return image
    
    except Exception as e:
        print(f"Error generating DALL-E 3 image: {e}")
        print("Creating fallback background...")
        return create_fallback_background()


def create_fallback_background():
    """Create a fallback background if DALL-E 3 fails"""
    
    # Create a dark, professional background
    img = Image.new('RGBA', (1024, 1024), color=(20, 20, 20, 255))
    draw = ImageDraw.Draw(img)
    
    # Add geometric elements
    for i in range(0, 1024, 50):
        draw.line([(i, 0), (i + 100, 1024)], fill=(40, 40, 40, 255), width=2)
    
    # Add corner accents
    corner_size = 80
    draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(1024, 0), (1024 - corner_size, 0), (1024, corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(0, 1024), (corner_size, 1024), (0, 1024 - corner_size)], fill=(255, 68, 68, 255))
    draw.polygon([(1024, 1024), (1024 - corner_size, 1024), (1024, 1024 - corner_size)], fill=(255, 68, 68, 255))
    
    return img


def create_professional_post(base_image, headline, subtext, cta_text):
    """Create professional post with text overlay using Pillow"""
    
    # Create a copy to work with
    final_image = base_image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Add dark overlay for text readability
    overlay = Image.new('RGBA', final_image.size, (0, 0, 0, 100))
    final_image = Image.alpha_composite(final_image, overlay)
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
    """Main orchestrator function with Gemini AI + DALL-E 3"""
    
    print("The Unseen Economy - Gemini + DALL-E 3 Hybrid Pipeline")
    print("=" * 60)
    
    # Setup
    constants = setup()
    gemini_model = constants['gemini_model']
    openai_client = constants['openai_client']
    
    try:
        # Step 1: Generate viral take with Gemini
        print("Generating viral take with Gemini AI...")
        take = generate_viral_take(gemini_model)
        print(f"Headline: {take['headline']}")
        print(f"Subtext: {take['subtext']}")
        
        # Step 2: Generate image prompt with Gemini
        print("Creating image prompt with Gemini...")
        theme = take['headline'] + ' ' + take['subtext']
        img_prompt = generate_image_prompt(theme, gemini_model)
        print(f"Image prompt: {img_prompt[:100]}...")
        
        # Step 3: Generate DALL-E 3 image
        print("Generating DALL-E 3 background image...")
        base_img = generate_dalle_image(img_prompt, openai_client)
        
        # Step 4: Create professional post with Pillow
        print("Creating professional post with Pillow...")
        cta = random.choice(constants['engagement_hooks'])
        final_image = create_professional_post(base_img, take['headline'], take['subtext'], cta)
        
        # Step 5: Save final image
        final_image.save('gemini_dalle_final_post.png')
        print("Successfully generated gemini_dalle_final_post.png")
        
        # Step 6: Generate hashtags
        hashtags = generate_hashtags(constants)
        
        # Print content for Facebook post
        print("\n" + "="*60)
        print("GEMINI + DALL-E 3 GENERATED CONTENT FOR FACEBOOK POST:")
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
            'ai_models': 'gemini-2.5-flash + dall-e-3'
        }
        
        with open('gemini_dalle_content_data.json', 'w') as f:
            json.dump(content_data, f, indent=2)
        
        print("Content data saved to gemini_dalle_content_data.json")
        
    except Exception as e:
        print(f"Error in Gemini + DALL-E 3 pipeline: {e}")
        return


if __name__ == "__main__":
    main()




