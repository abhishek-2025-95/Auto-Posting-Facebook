#!/usr/bin/env python3
"""
Quick status check for Imagen 4
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from datetime import datetime

def quick_status_check():
    """Quick check if Imagen 4 is ready"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Quick Imagen 4 status check...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='test',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                imageSize='2K',
                aspectRatio='1:1'
            )
        )
        
        if response.generated_images:
            print("SUCCESS: Imagen 4 is working!")
            return True
        else:
            print("No image generated")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "billed users" in error_msg:
            print("STATUS: Still waiting for billing to activate")
            print("This usually takes 5-30 minutes after activation")
        else:
            print(f"Error: {e}")
        return False

if __name__ == "__main__":
    quick_status_check()



