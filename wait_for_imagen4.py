#!/usr/bin/env python3
"""
Wait for Imagen 4 to be ready - checks every 5 minutes
"""

import time
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from config import GEMINI_API_KEY

def check_imagen4_ready():
    """Check if Imagen 4 is ready"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Imagen 4 status...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A simple test image',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                imageSize='2K',
                aspectRatio='1:1'
            )
        )
        
        if response.generated_images:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS! Imagen 4 is working!")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No image generated")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "billed users" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Still waiting for billing to activate...")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False

def main():
    """Main monitoring loop"""
    print("="*60)
    print("WAITING FOR IMAGEN 4 TO BE READY")
    print("="*60)
    print("Checking every 5 minutes...")
    print("Will start posting when Imagen 4 is working")
    print("="*60)
    
    while True:
        if check_imagen4_ready():
            print("\n" + "="*60)
            print("IMAGEN 4 IS READY! Starting automation...")
            print("="*60)
            
            # Import and run the main automation
            from main import run_automation_cycle
            run_automation_cycle()
            
            print("Automation started! Will post 5 times per day.")
            break
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting 5 minutes before next check...")
            time.sleep(300)  # Wait 5 minutes

if __name__ == "__main__":
    main()



