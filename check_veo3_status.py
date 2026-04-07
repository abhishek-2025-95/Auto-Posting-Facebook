#!/usr/bin/env python3
"""
Quick Veo 3 status check
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from datetime import datetime

def check_veo3_status():
    """Quick check if Veo 3 quota is available"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Veo 3 status...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test with a simple prompt
        test_prompt = "A simple test video"
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                negative_prompt="blurry",
            ),
        )
        
        print("SUCCESS: Veo 3 quota available!")
        return True
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print("STATUS: Quota exceeded - waiting for reset")
            print("This usually resets daily or with billing upgrade")
        else:
            print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_veo3_status()



