#!/usr/bin/env python3
"""
Create viral images with text embedded directly in the image
No links, just pure visual content
"""

from PIL import Image, ImageDraw, ImageFont
import os
import random
from facebook_poster import load_settings, FacebookPoster


def create_viral_image_with_text(text, filename="viral_image_with_text.jpg"):
    """Create a professional viral image with text embedded directly"""
    
    # Create image with optimal social media dimensions
    width, height = 1200, 630  # Facebook optimal size
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    
    # Try to use a bold font, fallback to default if not available
    try:
        # Try different font sizes and styles
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 32)
    except:
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
            subtitle_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
    
    # Split text into lines for better readability
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Check if line is too long (rough estimate)
        if len(' '.join(current_line)) > 25:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 4 lines for impact
    lines = lines[:4]
    
    # Calculate total text height
    line_height = 60
    total_height = len(lines) * line_height
    start_y = (height - total_height) // 2
    
    # Draw each line
    for i, line in enumerate(lines):
        # Get text size for centering
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text horizontally
        x = (width - text_width) // 2
        y = start_y + (i * line_height)
        
        # Draw text with outline for better readability
        # Draw black outline
        for adj in range(-2, 3):
            for adj2 in range(-2, 3):
                draw.text((x+adj, y+adj2), line, fill='black', font=title_font)
        
        # Draw white text
        draw.text((x, y), line, fill='white', font=title_font)
    
    # Add a subtle border
    draw.rectangle([0, 0, width-1, height-1], outline='red', width=3)
    
    # Save image
    image.save(filename)
    print(f"Viral image created: {filename}")
    return filename


def post_viral_image_to_facebook():
    """Create and post viral image with embedded text"""
    
    # Load settings
    settings = load_settings()
    poster = FacebookPoster(settings)
    
    # Viral content options
    viral_content = [
        "The top 1% captured 82% of all new wealth created last year, while the bottom 50% saw zero increase.",
        "The average CEO makes 350x more than their workers. In 1965, it was 20x.",
        "The 'free market' is a myth. 5 companies control 90% of what you consume.",
        "The 'American Dream' is now a subscription service. Everything became a monthly payment.",
        "The top 1% own more wealth than the bottom 90% combined.",
        "The average American has $90,000 in debt but only $8,000 in savings.",
        "The 'gig economy' isn't the future of work - it's the return of medieval serfdom.",
        "The minimum wage should be $25/hour, not $15. Here's the math that will make your head explode.",
        "Europe has better healthcare, education, and work-life balance than America, but Americans think they're 'freer.'",
        "The 'trickle-down economics' experiment has been running for 40 years. Here's what actually trickled down."
    ]
    
    # Select random viral content
    selected_text = random.choice(viral_content)
    
    # Create image with text embedded
    image_path = create_viral_image_with_text(selected_text)
    
    # Post to Facebook (no caption needed since text is in image)
    try:
        result = poster.post_image_from_path(image_path, caption="")
        print("Viral image posted successfully!")
        print(f"Post ID: {result['id']}")
        print(f"Content: {selected_text}")
        return result
    except Exception as e:
        print(f"Error posting image: {e}")
        return None


if __name__ == "__main__":
    print("Creating viral image with embedded text...")
    post_viral_image_to_facebook()




