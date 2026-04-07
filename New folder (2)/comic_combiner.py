"""
Comic Combiner: Combines multiple panel images into a single vertical comic strip.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)


def combine_panels_into_comic(image_paths, script_data, output_path, panel_width=1200):
    """
    Combine multiple panel images into a single vertical comic strip with proper comic styling.
    
    Args:
        image_paths (list): List of paths to panel images
        script_data (dict): Comic script containing panels with captions
        output_path (str): Path to save the combined comic image
        panel_width (int): Width of each panel in the final comic
        
    Returns:
        str: Path to the combined comic image, or None if combination fails
    """
    try:
        logger.info("Combining panels into single comic image...")
        
        if not image_paths:
            logger.error("No images to combine")
            return None
        
        panels = script_data.get("panels", [])
        comic_title = script_data.get("comic_title", "Daily News Comic")
        
        # Load all panel images
        panel_images = []
        for i, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                logger.warning(f"Image not found: {img_path}")
                continue
            
            try:
                img = Image.open(img_path)
                # Resize to consistent width while maintaining aspect ratio
                aspect_ratio = img.height / img.width
                new_height = int(panel_width * aspect_ratio)
                # Ensure minimum height for consistency
                if new_height < 600:
                    new_height = 600
                img = img.resize((panel_width, new_height), Image.Resampling.LANCZOS)
                panel_images.append((img, i))
            except Exception as e:
                logger.error(f"Error loading image {img_path}: {e}")
                continue
        
        if not panel_images:
            logger.error("No valid images to combine")
            return None
        
        # Try to load fonts
        try:
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/comic.ttf",
                "arial.ttf",
            ]
            title_font = None
            caption_font = None
            for font_path in font_paths:
                try:
                    if not title_font:
                        title_font = ImageFont.truetype(font_path, 36)
                    if not caption_font:
                        caption_font = ImageFont.truetype(font_path, 28)
                    break
                except:
                    continue
            if not title_font:
                title_font = ImageFont.load_default()
            if not caption_font:
                caption_font = ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            caption_font = ImageFont.load_default()
        
        # Calculate dimensions
        border_width = 8
        panel_spacing = 30
        caption_height = 100
        title_height = 80
        padding = 40
        
        # Calculate total height
        total_height = (
            title_height + padding +
            sum(img.height + caption_height + panel_spacing + (border_width * 2) for img, _ in panel_images) +
            padding
        )
        
        # Create the combined comic image with white background
        comic_width = panel_width + (padding * 2)
        comic_image = Image.new('RGB', (comic_width, total_height), color='white')
        draw = ImageDraw.Draw(comic_image)
        
        current_y = padding
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), comic_title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (comic_width - title_width) // 2
        draw.text((title_x, current_y), comic_title, fill='#1a1a1a', font=title_font)
        current_y += title_height + padding
        
        # Paste panels with borders and captions
        for img, idx in panel_images:
            panel_x = padding
            panel_y = current_y
            
            # Draw panel border (comic style - thick black border)
            border_rect = [
                panel_x - border_width,
                panel_y - border_width,
                panel_x + img.width + border_width,
                panel_y + img.height + border_width
            ]
            draw.rectangle(border_rect, fill='black', outline='black', width=border_width)
            
            # Paste the panel image inside the border
            comic_image.paste(img, (panel_x, panel_y))
            
            current_y += img.height + (border_width * 2)
            
            # Add caption below the panel (comic style)
            if idx < len(panels):
                caption = panels[idx].get("caption", "")
                if caption:
                    # Create caption box with rounded corners effect
                    caption_y = current_y
                    caption_box_height = caption_height
                    
                    # Draw caption background with border
                    caption_rect = [
                        panel_x - border_width,
                        caption_y,
                        panel_x + img.width + border_width,
                        caption_y + caption_box_height
                    ]
                    draw.rectangle(caption_rect, fill='#f8f8f8', outline='#333333', width=3)
                    
                    # Wrap caption text
                    words = caption.split()
                    lines = []
                    line = ""
                    max_width = img.width - 40
                    
                    for word in words:
                        test_line = line + word + " "
                        bbox = draw.textbbox((0, 0), test_line, font=caption_font)
                        if bbox[2] - bbox[0] < max_width:
                            line = test_line
                        else:
                            if line:
                                lines.append(line.strip())
                            line = word + " "
                    if line:
                        lines.append(line.strip())
                    
                    # Draw caption text (centered)
                    text_y = caption_y + 15
                    for line in lines[:4]:  # Limit to 4 lines
                        line_bbox = draw.textbbox((0, 0), line, font=caption_font)
                        line_width = line_bbox[2] - line_bbox[0]
                        line_x = panel_x + (img.width - line_width) // 2
                        draw.text((line_x, text_y), line, fill='#1a1a1a', font=caption_font)
                        text_y += 35
                    
                    current_y += caption_box_height
            
            # Add spacing between panels
            current_y += panel_spacing
        
        # Save the combined comic
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        comic_image.save(output_path, 'PNG', quality=95, optimize=True)
        
        logger.info(f"Successfully created combined comic: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error combining panels: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

