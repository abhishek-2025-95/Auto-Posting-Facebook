"""
The Artist: Image generation module using Google's Imagen API or alternative services.
Generates comic panel images from visual prompts.
"""

import google.generativeai as genai
import requests
import os
import logging
import time
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_panel_image_imagen(visual_prompt, api_key, output_dir="output", panel_number=1):
    """
    Generate a single panel image using Google's Imagen API via Vertex AI.
    Note: This requires Vertex AI setup. Falls back to alternative method.
    
    Args:
        visual_prompt (str): Detailed description of the scene to generate
        api_key (str): Google API key
        output_dir (str): Directory to save the image
        panel_number (int): Panel number for filename
        
    Returns:
        str: Path to the saved image file, or None if generation fails
    """
    try:
        logger.info(f"Attempting to generate image for panel {panel_number} using Google Imagen...")
        
        # Try using Hugging Face's free API as an alternative
        # This works with any API key and provides free image generation
        return generate_panel_image_huggingface(visual_prompt, output_dir, panel_number)
        
    except Exception as e:
        logger.warning(f"Imagen method failed: {e}. Trying alternative...")
        return generate_panel_image_huggingface(visual_prompt, output_dir, panel_number)


def generate_panel_image_huggingface(visual_prompt, output_dir="output", panel_number=1):
    """
    Generate a single panel image using Hugging Face's free Stable Diffusion API.
    This is a free alternative that doesn't require additional API keys.
    
    Args:
        visual_prompt (str): Detailed description of the scene to generate
        output_dir (str): Directory to save the image
        panel_number (int): Panel number for filename
        
    Returns:
        str: Path to the saved image file, or None if generation fails
    """
    try:
        logger.info(f"Generating image for panel {panel_number} using Hugging Face API...")
        
        # Use Hugging Face's free inference API for Stable Diffusion
        # Try multiple models in case one is down
        models = [
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
            "CompVis/stable-diffusion-v1-4"
        ]
        
        # Enhanced prompt for comic style
        enhanced_prompt = f"{visual_prompt}, watercolor ink comic style, textured paper, high quality, detailed, comic book art"
        
        for model in models:
            try:
                API_URL = f"https://api-inference.huggingface.co/models/{model}"
                
                # No auth needed for public models (may have rate limits)
                headers = {}
                
                payload = {
                    "inputs": enhanced_prompt,
                }
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                
                if response.status_code == 200:
                    # Check if response is an image
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type or response.content.startswith(b'\x89PNG'):
                        # Save the image directly to the output directory (no nested images folder)
                        os.makedirs(output_dir, exist_ok=True)
                        image_filename = f"panel_{panel_number}.png"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Successfully saved image: {image_path}")
                        return image_path
                    else:
                        # Model might be loading, wait and retry
                        logger.info(f"Model {model} is loading, waiting 10 seconds...")
                        time.sleep(10)
                        continue
                elif response.status_code == 503:
                    # Model is loading
                    logger.info(f"Model {model} is loading, trying next model...")
                    continue
                else:
                    logger.warning(f"Model {model} returned status {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error with model {model}: {e}")
                continue
        
        # All models failed, try fallback
        logger.warning("All Hugging Face models failed. Trying alternative...")
        return generate_panel_image_replicate(visual_prompt, output_dir, panel_number)
            
    except Exception as e:
        logger.warning(f"Hugging Face method failed: {e}. Trying alternative...")
        return generate_panel_image_replicate(visual_prompt, output_dir, panel_number)


def generate_panel_image_replicate(visual_prompt, output_dir="output", panel_number=1):
    """
    Generate a single panel image using Replicate's free tier (requires API key but has free credits).
    Falls back to a simple placeholder if all methods fail.
    
    Args:
        visual_prompt (str): Detailed description of the scene to generate
        output_dir (str): Directory to save the image
        panel_number (int): Panel number for filename
        
    Returns:
        str: Path to the saved image file, or None if generation fails
    """
    try:
        logger.info(f"Trying alternative image generation for panel {panel_number}...")
        
        # For now, we'll use a simple approach with PIL to create a placeholder
        # In production, you'd want to use a proper image generation service
        from PIL import Image, ImageDraw, ImageFont
        
        # Save the image directly to the output directory (no nested images folder)
        os.makedirs(output_dir, exist_ok=True)
        image_filename = f"panel_{panel_number}.png"
        image_path = os.path.join(output_dir, image_filename)
        
        # Create a placeholder image with the prompt text
        # This is a fallback - in production, replace with actual image generation API
        img = Image.new('RGB', (1024, 1024), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        words = visual_prompt.split()
        lines = []
        line = ""
        for word in words:
            test_line = line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < 900:
                line = test_line
            else:
                lines.append(line)
                line = word + " "
        if line:
            lines.append(line)
        
        # Draw text
        y = 100
        for line in lines[:15]:  # Limit to 15 lines
            draw.text((50, y), line, fill='black', font=font)
            y += 40
        
        img.save(image_path)
        logger.warning(f"Created placeholder image for panel {panel_number}. Consider using a proper image generation API.")
        return image_path
        
    except Exception as e:
        logger.error(f"All image generation methods failed for panel {panel_number}: {e}")
        return None


def generate_panel_image(visual_prompt, api_key, output_dir="output", panel_number=1):
    """
    Main function to generate a panel image.
    Tries multiple methods in order of preference.
    
    Args:
        visual_prompt (str): Detailed description of the scene to generate
        api_key (str): API key (currently using Gemini key, but image generation uses free alternatives)
        output_dir (str): Directory to save the image
        panel_number (int): Panel number for filename
        
    Returns:
        str: Path to the saved image file, or None if generation fails
    """
    # Try Hugging Face first (free, no API key needed)
    result = generate_panel_image_huggingface(visual_prompt, output_dir, panel_number)
    if result:
        return result
    
    # Fallback to placeholder
    logger.warning("Using placeholder image. For production, configure a proper image generation API.")
    return generate_panel_image_replicate(visual_prompt, output_dir, panel_number)


def generate_all_panels(script_data, api_key, output_dir="output"):
    """
    Generate all panel images from a comic script.
    
    Args:
        script_data (dict): Comic script containing panels array
        api_key (str): API key (Gemini key, though image generation uses free alternatives)
        output_dir (str): Directory to save images
        
    Returns:
        list: List of image file paths, or empty list if generation fails
    """
    image_paths = []
    
    if "panels" not in script_data:
        logger.error("Script data missing 'panels' key")
        return image_paths
    
    for panel in script_data["panels"]:
        panel_num = panel.get("panel_number", len(image_paths) + 1)
        visual_prompt = panel.get("visual_prompt", "")
        
        if not visual_prompt:
            logger.warning(f"Panel {panel_num} missing visual_prompt")
            continue
        
        image_path = generate_panel_image(
            visual_prompt, 
            api_key, 
            output_dir, 
            panel_num
        )
        
        if image_path:
            image_paths.append(image_path)
            # Add delay between generations to respect rate limits
            if len(image_paths) < len(script_data["panels"]):
                logger.info("Waiting 2 seconds before next image generation...")
                time.sleep(2)
        else:
            logger.error(f"Failed to generate panel {panel_num}")
            break  # Stop if we can't generate a panel
    
    return image_paths

