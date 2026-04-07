#!/usr/bin/env python3
"""
Create a simple image and post it to Facebook
"""

from PIL import Image, ImageDraw, ImageFont
import os
from facebook_poster import load_settings, FacebookPoster


def create_viral_image(text, filename="viral_image.jpg"):
    """Create a simple viral image with text"""
    
    # Create image
    width, height = 1200, 630
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Split text into lines
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Check if line is too long (rough estimate)
        if len(' '.join(current_line)) > 30:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text
    y_position = 50
    for line in lines[:5]:  # Limit to 5 lines
        # Get text size
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (width - text_width) // 2
        draw.text((x, y_position), line, fill='white', font=font)
        y_position += text_height + 10
    
    # Save image
    image.save(filename)
    print(f"Image created: {filename}")
    return filename


def post_image_to_facebook():
    """Create image and post to Facebook"""
    
    # Load settings
    settings = load_settings()
    poster = FacebookPoster(settings)
    
    # Create viral text
    viral_text = "The 'free market' is a myth. 5 companies control 90% of what you consume, and competition died in America."
    
    # Create image
    image_path = create_viral_image(viral_text)
    
    # Post to Facebook
    caption = f"{viral_text}\n\nWhat do they hide? This.\n\n#TheUnseenEconomy #TruthBomb #CorporateGreed #EconomicReality"
    
    try:
        result = poster.post_image_from_path(image_path, caption)
        print("Image posted successfully!")
        print(f"Post ID: {result['id']}")
        return result
    except Exception as e:
        print(f"Error posting image: {e}")
        return None


if __name__ == "__main__":
    print("Creating and posting viral image...")
    post_image_to_facebook()




