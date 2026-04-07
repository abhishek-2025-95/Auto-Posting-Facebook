#!/usr/bin/env python3
"""
Gemini Native Image Generation for Celebrity Viral Content
Uses the NEW Gemini image generation capabilities to create REAL celebrity images
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

def generate_celebrity_news(gemini_model):
    """Generate viral celebrity news using Gemini"""
    print("Generating viral celebrity news...")
    
    prompt = """
    You are a viral content creator for 'The Unseen Economy' Facebook page. 
    Generate a shocking, controversial celebrity news story that will go viral.
    
    Create a JSON response with:
    - "celebrity_name": The celebrity's name
    - "headline": A shocking, clickbait headline (5-10 words)
    - "subtext": The controversial details (15-20 words)
    - "scandal_type": The type of scandal (financial, corporate, economic)
    
    Make it about economic inequality, corporate greed, or wealth disparity.
    Target: US/Europe Millennials/Gen Z who are angry about economic injustice.
    
    Examples:
    - Celebrity CEO caught in wage theft scandal
    - Billionaire celebrity avoiding taxes while workers starve
    - Celebrity investor profiting from housing crisis
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up JSON response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        news = json.loads(content)
        return news
        
    except Exception as e:
        print(f"Error generating celebrity news: {e}")
        # Fallback content
        return {
            'celebrity_name': 'Blake Sterling',
            'headline': 'CEO Blake Sterling caught in wage theft scandal',
            'subtext': 'While workers earn minimum wage, he pockets millions in bonuses',
            'scandal_type': 'financial'
        }

def generate_celebrity_image_with_imagen(celebrity_name, headline):
    """Generate REAL celebrity image using Imagen 4 - Google's most advanced image model"""
    print(f"Generating REAL celebrity image using Imagen 4 for: {celebrity_name}")
    
    # Create a detailed prompt for Imagen 4
    image_prompt = f"""
    Professional headshot photograph of {celebrity_name}, a successful business executive and CEO.
    The image should be:
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
        print(f"Imagen 4 prompt: {image_prompt[:100]}...")
        
        # Use the new Google GenAI client for Imagen 4
        from google import genai
        from google.genai import types
        
        client = genai.Client()
        
        # Generate image using Imagen 4
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                imageSize='2K',  # High resolution
                aspectRatio='1:1',
                personGeneration='allow_adult'  # Allow adult person generation
            )
        )
        
        # Get the first generated image
        if response.generated_images:
            generated_image = response.generated_images[0]
            image_bytes = generated_image.image.imageBytes
            
            # Convert to PIL Image
            image = Image.open(BytesIO(image_bytes))
            print(f"Successfully generated REAL celebrity image with Imagen 4: {image.size}")
            return image
        else:
            print("No image generated by Imagen 4, creating fallback...")
            return create_fallback_celebrity_image(celebrity_name)
        
    except Exception as e:
        print(f"Error generating celebrity image with Imagen 4: {e}")
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
    print("Gemini Native Celebrity AI - REAL Celebrity Images")
    print("==================================================")
    
    # Setup
    constants = setup()
    gemini_model = constants['model']
    
    # Step 1: Generate celebrity news
    print("\n1. Generating celebrity news...")
    news = generate_celebrity_news(gemini_model)
    
    print(f"Celebrity: {news['celebrity_name']}")
    print(f"Headline: {news['headline']}")
    print(f"Subtext: {news['subtext']}")
    
    # Step 2: Generate REAL celebrity image using Imagen 4
    print("\n2. Generating REAL celebrity image with Imagen 4...")
    celebrity_image = generate_celebrity_image_with_imagen(news['celebrity_name'], news['headline'])
    
    # Step 3: Create viral post
    print("\n3. Creating viral post...")
    engagement_hook = random.choice(constants['engagement_hooks'])
    final_image = create_viral_post_image(celebrity_image, news['headline'], news['subtext'], engagement_hook)
    
    # Step 4: Generate hashtags
    hashtags = generate_hashtags(constants['hashtag_categories'])
    
    # Save final image
    output_filename = "gemini_celebrity_post.png"
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
    
    with open('gemini_celebrity_content.json', 'w') as f:
        json.dump(content_package, f, indent=2)
    
    print(f"\nContent package saved to gemini_celebrity_content.json")
    print(f"Image saved as {output_filename}")
    print(f"\nReady to post to Facebook!")

if __name__ == "__main__":
    main()
