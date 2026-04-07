#!/usr/bin/env python3
"""
Quick check if paid billing is fully active
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from datetime import datetime

def check_paid_status():
    """Quick check if paid billing is fully active"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking paid billing status...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test Veo 3 with a simple prompt
        test_prompt = "A simple test video"
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                negative_prompt="blurry",
            ),
        )
        
        print("SUCCESS: Paid billing fully active!")
        print("Veo 3 is working with your credits!")
        return True
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print("STATUS: Still waiting for billing propagation")
            print("This usually takes 5-30 minutes after upgrade")
        elif "billed users" in error_msg:
            print("STATUS: Still waiting for billing activation")
        else:
            print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_paid_status()



