#!/usr/bin/env python3
"""
Simple Subtitle Enhancer - Add viral text overlays using PIL
"""

from PIL import Image, ImageDraw, ImageFont
import os
import re
from datetime import datetime

def extract_key_phrases(text, max_phrases=4):
    """Extract key phrases from text for subtitles"""
    # Remove hashtags and clean text
    clean_text = re.sub(r'#\w+', '', text)
    clean_text = re.sub(r'http\S+', '', clean_text)
    clean_text = clean_text.strip()
    
    # Split into sentences and extract key phrases
    sentences = [s.strip() for s in clean_text.split('.') if s.strip()]
    
    # Take first few sentences as key phrases
    key_phrases = sentences[:max_phrases]
    
    # Add some viral-style phrases
    viral_phrases = [
        "BREAKING NEWS",
        "MAJOR ALERT", 
        "YOU NEED TO KNOW",
        "SHARE THIS NOW"
    ]
    
    # Combine viral phrases with content
    subtitle_phrases = []
    if key_phrases:
        subtitle_phrases.append(viral_phrases[0])
        subtitle_phrases.extend(key_phrases[:2])
        if len(key_phrases) > 2:
            subtitle_phrases.append(viral_phrases[1])
    
    return subtitle_phrases

def create_viral_image_with_text(image_path, caption_text, output_path):
    """Create a viral image with text overlays"""
    print("Creating viral image with text overlays...")
    
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to standard social media size
        image = image.resize((1080, 1080), Image.Resampling.LANCZOS)
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)
        
        # Extract key phrases
        phrases = extract_key_phrases(caption_text)
        
        # Try to load a bold font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_medium = ImageFont.truetype("arial.ttf", 40)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Add text overlays
        y_position = 50
        
        for i, phrase in enumerate(phrases):
            # Choose font size based on position
            font = font_large if i == 0 else font_medium
            
            # Create text with outline
            text = phrase.upper()
            
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x_position = (1080 - text_width) // 2
            
            # Draw text outline (black)
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x_position + dx, y_position + dy), text, font=font, fill='black')
            
            # Draw main text (white or yellow)
            color = 'yellow' if i == 0 else 'white'
            draw.text((x_position, y_position), text, font=font, fill=color)
            
            # Move down for next line
            y_position += text_height + 20
        
        # Add a pulsing effect to the first text (make it slightly larger)
        if phrases:
            # Redraw the first phrase with a slight size increase
            first_phrase = phrases[0].upper()
            try:
                font_pulse = ImageFont.truetype("arial.ttf", 65)
            except:
                font_pulse = font_large
            
            bbox = draw.textbbox((0, 0), first_phrase, font=font_pulse)
            text_width = bbox[2] - bbox[0]
            x_position = (1080 - text_width) // 2
            
            # Draw outline
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x_position + dx, 50 + dy), first_phrase, font=font_pulse, fill='black')
            
            # Draw main text
            draw.text((x_position, 50), first_phrase, font=font_pulse, fill='yellow')
        
        # Save the enhanced image
        image.save(output_path, 'JPEG', quality=95)
        
        print(f"SUCCESS: Viral image with text saved as {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error creating viral image: {e}")
        return None

def create_enhanced_content_with_text(article):
    """Create enhanced content with viral text overlays"""
    print("Creating enhanced content with viral text...")
    
    try:
        from content_generator import generate_facebook_caption, generate_post_image_fallback
        
        # Generate caption
        caption = generate_facebook_caption(article)
        
        # Generate base image
        base_image = generate_post_image_fallback(article)
        
        if not base_image:
            print("Failed to generate base image")
            return None
        
        # Add viral text overlays
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        enhanced_image = f"viral_image_{timestamp}.jpg"
        
        result = create_viral_image_with_text(base_image, caption, enhanced_image)
        
        if result:
            # Clean up base image
            try:
                os.remove(base_image)
            except:
                pass
            
            return result
        else:
            return base_image
            
    except Exception as e:
        print(f"Error creating enhanced content: {e}")
        return None

if __name__ == "__main__":
    # Test with sample content
    test_article = {
        'title': 'Major Tech Company Faces Data Breach Scandal',
        'description': 'Millions of user records exposed in what experts call the largest breach of 2024'
    }
    
    result = create_enhanced_content_with_text(test_article)
    if result:
        print(f"Enhanced image created: {result}")
    else:
        print("Failed to create enhanced image")



