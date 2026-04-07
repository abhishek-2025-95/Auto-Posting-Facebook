#!/usr/bin/env python3
"""
Check Google Cloud billing status
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from datetime import datetime

def check_billing_status():
    """Check billing status and API access"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking billing status...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test different models to see what's available
        print("Testing Gemini text generation...")
        try:
            # This should work on free tier
            from google.generativeai import GenerativeModel
            import google.generativeai as genai_text
            genai_text.configure(api_key=GEMINI_API_KEY)
            model = genai_text.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content("Test")
            print("SUCCESS: Gemini text: Working")
        except Exception as e:
            print(f"ERROR: Gemini text: {e}")
        
        print("\nTesting Imagen 4...")
        try:
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt='test',
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    imageSize='2K',
                    aspectRatio='1:1'
                )
            )
            print("SUCCESS: Imagen 4: Working")
        except Exception as e:
            error_msg = str(e)
            if "billed users" in error_msg:
                print("ERROR: Imagen 4: Requires paid billing")
            else:
                print(f"ERROR: Imagen 4: {e}")
        
        print("\nTesting Veo 3...")
        try:
            operation = client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt="test",
                config=types.GenerateVideosConfig(
                    negative_prompt="blurry",
                ),
            )
            print("SUCCESS: Veo 3: Working")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                print("ERROR: Veo 3: Quota exceeded (free tier)")
            elif "billed users" in error_msg:
                print("ERROR: Veo 3: Requires paid billing")
            else:
                print(f"ERROR: Veo 3: {e}")
        
        print("\n" + "="*50)
        print("BILLING STATUS SUMMARY:")
        print("="*50)
        print("You have credits but may still be on free tier")
        print("To use Veo 3 and Imagen 4, you need to:")
        print("1. Go to Google Cloud Console")
        print("2. Upgrade to a paid plan")
        print("3. Add a payment method")
        print("4. This will unlock your credits for use")
        
    except Exception as e:
        print(f"Error checking billing: {e}")

if __name__ == "__main__":
    check_billing_status()
