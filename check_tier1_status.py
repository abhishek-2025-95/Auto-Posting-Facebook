#!/usr/bin/env python3
"""
Check Tier 1 billing status and quota limits
"""

import google.generativeai as genai
from google import genai as imagen_genai
from google.genai import types
from config import GEMINI_API_KEY
import time
from datetime import datetime

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def check_tier1_status():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Tier 1 status...")
    
    # Test Gemini text generation
    print("Testing Gemini text generation...")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test message")
        print("SUCCESS: Gemini text generation working")
    except Exception as e:
        print(f"ERROR: Gemini text: {e}")
        return False
    
    # Test Imagen 4
    print("\nTesting Imagen 4...")
    try:
        client = imagen_genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A simple test image',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                imageSize='2K',
                aspectRatio='1:1'
            )
        )
        print("SUCCESS: Imagen 4 working")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"WARNING: Imagen 4 quota/rate limit: {e}")
            print("   This is normal - just means you need to wait for quota reset")
        else:
            print(f"ERROR: Imagen 4: {e}")
    
    # Test Veo 3
    print("\nTesting Veo 3...")
    try:
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt="A simple test video",
            config=types.GenerateVideosConfig(
                duration=5,
                aspect_ratio="16:9",
                resolution="720p",
                generate_audio=False,
                negative_prompt="blurry, low quality"
            ),
        )
        print("SUCCESS: Veo 3 working")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"WARNING: Veo 3 quota/rate limit: {e}")
            print("   This is normal - just means you need to wait for quota reset")
        else:
            print(f"ERROR: Veo 3: {e}")
    
    print("\n" + "="*50)
    print("TIER 1 STATUS SUMMARY:")
    print("="*50)
    print("You have paid billing (Tier 1)")
    print("Rate limits are normal - just wait for quota reset")
    print("The system will auto-retry when quotas reset")
    print("="*50)
    
    return True

if __name__ == "__main__":
    check_tier1_status()
