#!/usr/bin/env python3
"""
Gemini Nano Banana Celebrity AI - Working Version
Uses fallback content when quota limits are hit, but ready for REAL images when billing is enabled
"""

import os
import json
import random
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import google.generativeai as genai

def setup():
    """Initialize Gemini AI client"""
    # Configure Gemini with your API key
    genai.configure(api_key="AIzaSyBt2KV8_nOKdpG14Pf92CT1-8L48dUZk2o")
    
    # Use the NEW Gemini image generation model
    model = genai.GenerativeModel('gemini-2.5-flash-image')
    
    # Engagement hooks for viral content
    ENGAGEMENT_HOOKS = [
        "SHARE IF THIS MAKES YOU ANGRY",
        "SHARE IF YOU'RE TIRED OF BEING BLAMED", 
        "SHARE IF YOU'RE READY FOR CHANGE",
        "IS THIS THE 'OPPORTUNITY' THEY PROMISED?",
        "WHAT DO THEY HIDE? THIS.",
        "SHARE IF THIS SHOCKS YOU",
        "SHARE IF YOU'RE FED UP",
        "SHARE IF YOU'RE OUTRAGED",
        "SHARE IF YOU'RE FURIOUS",
        "SHARE IF THIS MAKES YOU MAD"
    ]
    
    # Hashtag categories
    HASHTAG_CATEGORIES = {
        'Viral': ['#ViralTake', '#TruthBomb', '#DataBomb', '#MindBlown', '#TheUnseenEconomy', '#BreakingNews', '#Trending', '#ViralNews', '#Scandal', '#Shocking', '#Exposed', '#Outrage'],
        'Controversial': ['#EconomicReality', '#WealthInequality', '#CorporateGreed', '#LateStageCapitalism', '#Justice', '#Accountability', '#CelebrityCrime'],
        'Problem-Focused': ['#HousingCrisis', '#DebtCrisis', '#Healthcare', '#GigEconomy', '#Inflation']
    }
    
    return {
        'model': model,
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES
    }

def generate_celebrity_news():
    """Generate viral celebrity news (using fallback due to quota limits)"""
    print("Generating viral celebrity news...")
    
    # Fallback celebrity news (since API quota exceeded)
    celebrity_news = [
        {
            'celebrity_name': 'Blake Sterling',
            'headline': 'CEO Blake Sterling caught in wage theft scandal',
            'subtext': 'While workers earn minimum wage, he pockets millions in bonuses',
            'scandal_type': 'financial'
        },
        {
            'celebrity_name': 'Victoria Chen',
            'headline': 'Tech CEO Victoria Chen avoids $50M in taxes',
            'subtext': 'While her employees struggle with student debt, she hides money offshore',
            'scandal_type': 'tax_evasion'
        },
        {
            'celebrity_name': 'Marcus Rodriguez',
            'headline': 'Billionaire Marcus Rodriguez profits from housing crisis',
            'subtext': 'Buys up affordable housing, then rents it back at triple the price',
            'scandal_type': 'housing'
        },
        {
            'celebrity_name': 'Sarah Thompson',
            'headline': 'CEO Sarah Thompson fires 1000 workers for AI',
            'subtext': 'Replaces human workers with robots while pocketing $200M bonus',
            'scandal_type': 'automation'
        },
        {
            'celebrity_name': 'David Kim',
            'headline': 'Billionaire David Kim exploits gig workers',
            'subtext': 'Makes $2B while drivers earn less than minimum wage',
            'scandal_type': 'gig_economy'
        }
    ]
    
    return random.choice(celebrity_news)

def generate_celebrity_image_with_gemini_nano_banana(gemini_model, celebrity_name, headline):
    """Generate REAL celebrity image using Gemini Nano Banana (gemini-2.5-flash-image)"""
    print(f"Generating REAL celebrity image using Gemini Nano Banana for: {celebrity_name}")
    
    # Create a detailed prompt for Gemini Nano Banana
    image_prompt = f"""
    Create a picture of a professional headshot photograph of {celebrity_name}, 
    a successful business executive and CEO. The image should be:
    - Photorealistic and high-quality
    - Professional business headshot style
    - Confident, authoritative expression
    - Professional business attire (suit and tie)
    - Clean, corporate background
    - Studio lighting quality
    - High-resolution, suitable for news articles
    - 35mm portrait photography style
    """
    
    try:
        print(f"Gemini Nano Banana prompt: {image_prompt[:100]}...")
        
        # Use Gemini's native image generation
        response = gemini_model.generate_content(image_prompt)
        
        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # Convert base64 to image
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                print(f"Successfully generated REAL celebrity image with Gemini Nano Banana: {image.size}")
                return image
            elif part.text is not None:
                print(f"Text response: {part.text}")
        
        print("No image generated by Gemini Nano Banana, creating fallback...")
        return create_fallback_celebrity_image(celebrity_name)
        
    except Exception as e:
        print(f"Error generating celebrity image with Gemini Nano Banana: {e}")
        print("Creating fallback celebrity image...")
        return create_fallback_celebrity_image(celebrity_name)

def create_fallback_celebrity_image(celebrity_name):
    """Create a sophisticated fallback celebrity image"""
    print(f"Creating sophisticated fallback for {celebrity_name}")
    
    # Create a professional-looking placeholder
    img = Image.new('RGB', (1024, 1024), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Add professional elements
    # Background gradient
    for y in range(1024):
        color_value = int(26 + (y / 1024) * 50)
        draw.line([(0, y), (1024, y)], fill=(color_value, color_value, color_value))
    
    # Add professional silhouette
    draw.ellipse([200, 200, 824, 824], fill='#2d2d2d', outline='#4a4a4a', width=3)
    
    # Add name
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Center the name
    bbox = draw.textbbox((0, 0), celebrity_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (1024 - text_width) // 2
    draw.text((text_x, 900), celebrity_name, fill='white', font=font)
    
    return img

def create_viral_post_image(celebrity_image, headline, subtext, engagement_hook):
    """Create the final viral post image with celebrity photo and text overlay"""
    print("Creating viral post image...")
    
    # Resize celebrity image to fit
    celebrity_image = celebrity_image.resize((1024, 1024), Image.Resampling.LANCZOS)
    
    # Create overlay for text
    overlay = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Add semi-transparent background for text
    draw.rectangle([0, 700, 1024, 1024], fill=(0, 0, 0, 180))
    
    # Add headline
    try:
        headline_font = ImageFont.truetype("arial.ttf", 36)
        subtext_font = ImageFont.truetype("arial.ttf", 24)
        hook_font = ImageFont.truetype("arial.ttf", 28)
    except:
        headline_font = ImageFont.load_default()
        subtext_font = ImageFont.load_default()
        hook_font = ImageFont.load_default()
    
    # Headline
    draw.text((50, 720), headline, fill='white', font=headline_font)
    
    # Subtext
    draw.text((50, 770), subtext, fill='#cccccc', font=subtext_font)
    
    # Engagement hook
    draw.text((50, 820), engagement_hook, fill='#ff4444', font=hook_font)
    
    # Combine images
    if celebrity_image.mode != 'RGBA':
        celebrity_image = celebrity_image.convert('RGBA')
    
    final_image = Image.alpha_composite(celebrity_image, overlay)
    return final_image.convert('RGB')

def generate_hashtags(hashtag_categories):
    """Generate relevant hashtags"""
    hashtags = []
    
    # Add 2-3 viral hashtags
    hashtags.extend(random.sample(hashtag_categories['Viral'], 3))
    
    # Add 2 controversial hashtags
    hashtags.extend(random.sample(hashtag_categories['Controversial'], 2))
    
    # Add 1-2 problem-focused hashtags
    hashtags.extend(random.sample(hashtag_categories['Problem-Focused'], 2))
    
    return ' '.join(hashtags)

def main():
    print("Gemini Nano Banana Celebrity AI - REAL Celebrity Images")
    print("======================================================")
    
    # Setup
    constants = setup()
    gemini_model = constants['model']
    
    # Step 1: Generate celebrity news
    print("\n1. Generating celebrity news...")
    news = generate_celebrity_news()
    
    print(f"Celebrity: {news['celebrity_name']}")
    print(f"Headline: {news['headline']}")
    print(f"Subtext: {news['subtext']}")
    
    # Step 2: Generate REAL celebrity image using Gemini Nano Banana
    print("\n2. Generating REAL celebrity image with Gemini Nano Banana...")
    celebrity_image = generate_celebrity_image_with_gemini_nano_banana(gemini_model, news['celebrity_name'], news['headline'])
    
    # Step 3: Create viral post
    print("\n3. Creating viral post...")
    engagement_hook = random.choice(constants['engagement_hooks'])
    final_image = create_viral_post_image(celebrity_image, news['headline'], news['subtext'], engagement_hook)
    
    # Step 4: Generate hashtags
    hashtags = generate_hashtags(constants['hashtag_categories'])
    
    # Save final image
    output_filename = "gemini_nano_banana_celebrity_post.png"
    final_image.save(output_filename)
    print(f"\nSuccessfully generated {output_filename}")
    
    # Generate Facebook post text
    post_text = f"{news['headline']}\n\n{news['subtext']}\n\n{engagement_hook}\n\n{hashtags}"
    
    print(f"\nFacebook Post Text:")
    print("=" * 50)
    print(post_text)
    print("=" * 50)
    
    # Save content package
    content_package = {
        'celebrity_name': news['celebrity_name'],
        'headline': news['headline'],
        'subtext': news['subtext'],
        'engagement_hook': engagement_hook,
        'hashtags': hashtags,
        'post_text': post_text,
        'image_file': output_filename,
        'generated_at': datetime.now().isoformat()
    }
    
    with open('gemini_nano_banana_content.json', 'w') as f:
        json.dump(content_package, f, indent=2)
    
    print(f"\nContent package saved to gemini_nano_banana_content.json")
    print(f"Image saved as {output_filename}")
    print(f"\nReady to post to Facebook!")

if __name__ == "__main__":
    main()




