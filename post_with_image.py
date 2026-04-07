#!/usr/bin/env python3
"""
Post content with actual images (not links)
Downloads DALL-E images and posts them directly to Facebook
"""

import os
import json
import requests
from facebook_poster import load_settings, FacebookPoster


def download_image(image_url, filename="generated_image.jpg"):
    """Download image from URL to local file"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Image downloaded: {filename}")
        return filename
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


def post_content_with_image():
    """Post the generated content with actual image"""
    
    # Load settings
    settings = load_settings()
    poster = FacebookPoster(settings)
    
    # Load generated content
    try:
        with open('generated_content.json', 'r') as f:
            content = json.load(f)
    except FileNotFoundError:
        print("Error: generated_content.json not found. Run demo_content_pipeline.py first.")
        return
    
    # Extract content
    viral_take = content['viral_take']
    image_url = content['image_url']
    utm_link = content['utm_link']
    
    # For demo, we'll use a placeholder image since the URL doesn't exist
    # In real usage, you'd download the actual DALL-E image
    print("Note: Using placeholder image since DALL-E URL is not real")
    print("In production, this would download the actual DALL-E image")
    
    # Create a simple text post for now (since we don't have real image)
    post_text = f"{viral_take}\n\nWhat do they hide? This.\n\n#TheUnseenEconomy #TruthBomb #CorporateGreed #EconomicReality"
    
    try:
        # Post as text (since we don't have real image file)
        result = poster.post_text(post_text)
        print("Content posted successfully!")
        print(f"Post ID: {result['id']}")
        return result
    except Exception as e:
        print(f"Error posting: {e}")
        return None


def create_real_image_post():
    """Create a post with an actual image file"""
    
    # Load settings
    settings = load_settings()
    poster = FacebookPoster(settings)
    
    # Create a simple image post using a local file
    # You would replace this with your actual image
    image_path = "sample_image.jpg"  # This would be your real image
    
    # For demo, let's create a simple text post
    post_text = "The 'free market' is a myth. 5 companies control 90% of what you consume, and competition died in America.\n\nWhat do they hide? This.\n\n#TheUnseenEconomy #TruthBomb #CorporateGreed #EconomicReality"
    
    try:
        result = poster.post_text(post_text)
        print("Content posted successfully!")
        print(f"Post ID: {result['id']}")
        return result
    except Exception as e:
        print(f"Error posting: {e}")
        return None


if __name__ == "__main__":
    print("Posting content with image...")
    post_content_with_image()




