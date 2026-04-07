#!/usr/bin/env python3
"""
Enhanced Viral Designer - Professional storytelling graphics
High-impact visual content with enhanced design elements
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math
from facebook_poster import load_settings, FacebookPoster


def create_enhanced_viral_image(text, filename="enhanced_viral_image.jpg"):
    """Create a professional, storytelling viral image with enhanced graphics"""
    
    # Create high-resolution image for better quality
    width, height = 1200, 630
    image = Image.new('RGB', (width, height), color='#0a0a0a')  # Dark background
    draw = ImageDraw.Draw(image)
    
    # Enhanced design elements
    def draw_gradient_background():
        """Create a dramatic gradient background"""
        for y in range(height):
            # Create gradient from dark to darker
            intensity = int(255 * (1 - y / height) * 0.3)
            color = (intensity, intensity, intensity)
            draw.line([(0, y), (width, y)], fill=color)
    
    def draw_geometric_elements():
        """Add geometric design elements"""
        # Draw diagonal lines for dynamic feel
        for i in range(0, width, 50):
            draw.line([(i, 0), (i + 100, height)], fill='#1a1a1a', width=2)
        
        # Add corner accents
        corner_size = 80
        draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill='#ff4444')
        draw.polygon([(width, 0), (width - corner_size, 0), (width, corner_size)], fill='#ff4444')
        draw.polygon([(0, height), (corner_size, height), (0, height - corner_size)], fill='#ff4444')
        draw.polygon([(width, height), (width - corner_size, height), (width, height - corner_size)], fill='#ff4444')
    
    def draw_data_visualization():
        """Add data visualization elements"""
        # Draw a dramatic bar chart in the background
        bar_width = 20
        bar_spacing = 30
        start_x = 50
        start_y = height - 100
        
        # Create unequal bars to represent wealth inequality
        bars = [5, 8, 12, 20, 35, 80, 200]  # Heights representing wealth distribution
        
        for i, bar_height in enumerate(bars):
            x = start_x + (i * (bar_width + bar_spacing))
            y = start_y - bar_height
            
            # Color bars based on height (wealth)
            if bar_height > 50:
                color = '#ff4444'  # Red for high wealth
            elif bar_height > 20:
                color = '#ffaa44'  # Orange for medium wealth
            else:
                color = '#444444'  # Gray for low wealth
            
            draw.rectangle([x, y, x + bar_width, start_y], fill=color)
    
    def draw_text_with_enhanced_typography():
        """Create enhanced typography with better storytelling"""
        # Try to load better fonts
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
            subtitle_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
            accent_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            accent_font = ImageFont.load_default()
        
        # Split text into main message and supporting details
        words = text.split()
        main_message = []
        supporting_details = []
        
        # Split into main message (first 8-10 words) and details
        if len(words) > 10:
            main_message = words[:8]
            supporting_details = words[8:]
        else:
            main_message = words[:5]
            supporting_details = words[5:]
        
        main_text = ' '.join(main_message)
        detail_text = ' '.join(supporting_details)
        
        # Draw main message with dramatic styling
        main_bbox = draw.textbbox((0, 0), main_text, font=title_font)
        main_width = main_bbox[2] - main_bbox[0]
        main_height = main_bbox[3] - main_bbox[1]
        
        main_x = (width - main_width) // 2
        main_y = height // 2 - 80
        
        # Draw text shadow for depth
        shadow_offset = 3
        draw.text((main_x + shadow_offset, main_y + shadow_offset), main_text, 
                 fill='#000000', font=title_font)
        
        # Draw main text with gradient effect
        draw.text((main_x, main_y), main_text, fill='#ffffff', font=title_font)
        
        # Draw supporting details
        if detail_text:
            detail_bbox = draw.textbbox((0, 0), detail_text, font=subtitle_font)
            detail_width = detail_bbox[2] - detail_bbox[0]
            detail_x = (width - detail_width) // 2
            detail_y = main_y + main_height + 20
            
            draw.text((detail_x, detail_y), detail_text, fill='#cccccc', font=subtitle_font)
        
        # Add call-to-action text
        cta_text = "SHARE IF THIS MAKES YOU ANGRY"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=accent_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        cta_x = (width - cta_width) // 2
        cta_y = height - 60
        
        # Draw CTA with red background
        padding = 10
        draw.rectangle([cta_x - padding, cta_y - padding, cta_x + cta_width + padding, cta_y + 30 + padding], 
                      fill='#ff4444')
        draw.text((cta_x, cta_y), cta_text, fill='#ffffff', font=accent_font)
    
    def draw_visual_elements():
        """Add visual storytelling elements"""
        # Draw a dramatic diagonal line
        draw.line([(0, height//2), (width, height//2 + 100)], fill='#ff4444', width=4)
        
        # Add percentage indicators
        draw.text((50, 50), "1%", fill='#ff4444', font=ImageFont.load_default())
        draw.text((width - 100, height - 100), "99%", fill='#666666', font=ImageFont.load_default())
        
        # Add visual arrows pointing to inequality
        arrow_size = 20
        # Arrow pointing up (wealth)
        draw.polygon([(width//2 - arrow_size, 100), (width//2 + arrow_size, 100), (width//2, 60)], fill='#ff4444')
        # Arrow pointing down (poverty)
        draw.polygon([(width//2 - arrow_size, height - 100), (width//2 + arrow_size, height - 100), (width//2, height - 60)], fill='#666666')
    
    # Build the enhanced image
    draw_gradient_background()
    draw_geometric_elements()
    draw_data_visualization()
    draw_text_with_enhanced_typography()
    draw_visual_elements()
    
    # Add final border
    draw.rectangle([0, 0, width-1, height-1], outline='#ff4444', width=4)
    
    # Save with high quality
    image.save(filename, quality=95)
    print(f"Enhanced viral image created: {filename}")
    return filename


def create_storytelling_viral_image(text, filename="storytelling_viral.jpg"):
    """Create a storytelling-focused viral image with narrative elements"""
    
    width, height = 1200, 630
    image = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(image)
    
    # Create a narrative layout
    def draw_story_background():
        """Create a storytelling background"""
        # Draw a city skyline silhouette
        building_heights = [200, 150, 300, 100, 250, 180, 320, 120, 280, 160]
        building_x = 0
        for height in building_heights:
            draw.rectangle([building_x, height - height, building_x + 60, height], 
                          fill='#333333')
            building_x += 60
        
        # Add a dramatic sky gradient
        for y in range(height//3):
            intensity = int(100 * (1 - y / (height//3)))
            color = (intensity, intensity//2, 0)
            draw.line([(0, y), (width, y)], fill=color)
    
    def draw_narrative_text():
        """Create narrative text layout"""
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 48)
            story_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            story_font = ImageFont.load_default()
        
        # Main headline
        headline = "THE UNSEEN ECONOMY"
        headline_bbox = draw.textbbox((0, 0), headline, font=title_font)
        headline_width = headline_bbox[2] - headline_bbox[0]
        headline_x = (width - headline_width) // 2
        headline_y = 50
        
        # Draw headline with glow effect
        for i in range(5):
            draw.text((headline_x - i, headline_y - i), headline, fill='#ff4444', font=title_font)
        draw.text((headline_x, headline_y), headline, fill='#ffffff', font=title_font)
        
        # Main story text
        story_text = text
        words = story_text.split()
        
        # Create story paragraphs
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 25:
                lines.append(' '.join(current_line))
                current_line = []
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw story lines
        line_y = 150
        for line in lines[:4]:  # Limit to 4 lines
            line_bbox = draw.textbbox((0, 0), line, font=story_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            
            # Draw text with shadow
            draw.text((line_x + 2, line_y + 2), line, fill='#000000', font=story_font)
            draw.text((line_x, line_y), line, fill='#ffffff', font=story_font)
            line_y += 40
        
        # Add emotional hook
        hook_text = "THIS IS WHY WE'RE ANGRY"
        hook_bbox = draw.textbbox((0, 0), hook_text, font=title_font)
        hook_width = hook_bbox[2] - hook_bbox[0]
        hook_x = (width - hook_width) // 2
        hook_y = height - 100
        
        # Draw hook with red background
        padding = 15
        draw.rectangle([hook_x - padding, hook_y - padding, hook_x + hook_width + padding, hook_y + 50 + padding], 
                      fill='#ff4444')
        draw.text((hook_x, hook_y), hook_text, fill='#ffffff', font=title_font)
    
    def draw_visual_story_elements():
        """Add visual storytelling elements"""
        # Draw a scale showing inequality
        scale_x = width // 2
        scale_y = height // 2
        
        # Scale base
        draw.line([(scale_x - 100, scale_y), (scale_x + 100, scale_y)], fill='#666666', width=8)
        
        # Left side (99%)
        draw.rectangle([scale_x - 120, scale_y - 20, scale_x - 100, scale_y], fill='#666666')
        draw.text((scale_x - 140, scale_y - 40), "99%", fill='#666666', font=ImageFont.load_default())
        
        # Right side (1%)
        draw.rectangle([scale_x + 100, scale_y - 80, scale_x + 120, scale_y], fill='#ff4444')
        draw.text((scale_x + 130, scale_y - 100), "1%", fill='#ff4444', font=ImageFont.load_default())
        
        # Add dramatic lighting effect
        for i in range(20):
            alpha = 255 - (i * 10)
            draw.ellipse([scale_x - i*10, scale_y - i*10, scale_x + i*10, scale_y + i*10], 
                        outline=(255, 255, 255, alpha), width=2)
    
    # Build the storytelling image
    draw_story_background()
    draw_narrative_text()
    draw_visual_story_elements()
    
    # Add final touches
    draw.rectangle([0, 0, width-1, height-1], outline='#ff4444', width=6)
    
    image.save(filename, quality=95)
    print(f"Storytelling viral image created: {filename}")
    return filename


def post_enhanced_viral_image():
    """Create and post enhanced viral image"""
    
    # Load settings
    settings = load_settings()
    poster = FacebookPoster(settings)
    
    # Enhanced viral content with storytelling focus
    viral_stories = [
        "The top 1% captured 82% of all new wealth created last year, while the bottom 50% saw zero increase.",
        "The average CEO makes 350x more than their workers. In 1965, it was 20x. This isn't meritocracy - it's aristocracy with better PR.",
        "The 'free market' is a myth. 5 companies control 90% of what you consume, and competition died in America.",
        "The 'American Dream' is now a subscription service. Everything became a monthly payment, and you're paying more for less.",
        "The top 1% own more wealth than the bottom 90% combined. This isn't capitalism - it's feudalism with better technology.",
        "The average American has $90,000 in debt but only $8,000 in savings. This isn't personal failure - it's systemic design.",
        "The 'gig economy' isn't the future of work - it's the return of medieval serfdom with better marketing.",
        "The minimum wage should be $25/hour, not $15. Here's the math that will make your head explode.",
        "Europe has better healthcare, education, and work-life balance than America, but Americans think they're 'freer.' The propaganda is working perfectly.",
        "The 'trickle-down economics' experiment has been running for 40 years. Here's what actually trickled down (spoiler: it's not money)."
    ]
    
    # Select random story
    selected_story = random.choice(viral_stories)
    
    # Create enhanced image
    image_path = create_enhanced_viral_image(selected_story)
    
    # Post to Facebook
    try:
        result = poster.post_image_from_path(image_path, caption="")
        print("Enhanced viral image posted successfully!")
        print(f"Post ID: {result['id']}")
        print(f"Story: {selected_story}")
        return result
    except Exception as e:
        print(f"Error posting image: {e}")
        return None


if __name__ == "__main__":
    print("Creating enhanced viral image with storytelling design...")
    post_enhanced_viral_image()




