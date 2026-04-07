#!/usr/bin/env python3
"""
Wait for Veo 3 to be ready - checks every 5 minutes
"""

import time
from datetime import datetime
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

def check_veo3_ready():
    """Check if Veo 3 is ready"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Veo 3 status...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test with a simple prompt
        test_prompt = "A simple test video of a red ball bouncing"
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                duration=2,  # Short test video
                aspect_ratio="16:9",
                resolution="720p",  # Lower resolution for testing
                generate_audio=False  # No audio for faster testing
            )
        )
        
        # Check if operation started successfully
        if operation:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS! Veo 3 is working!")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No operation started")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "billed users" in error_msg or "quota" in error_msg.lower():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Still waiting for billing to activate...")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False

def start_automation_when_ready():
    """Start the main automation once Veo 3 is working"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Veo 3 is ready! Starting full automation...")
    
    # Import and run the main automation
    from main import run_automation_cycle
    run_automation_cycle()
    
    # Schedule regular posts
    import schedule
    schedule.every(288).minutes.do(run_automation_cycle)  # Every 4.8 hours (5 times per day)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Full automation started! Will post 5 times per day with 8-second videos.")

def main():
    """Main monitoring loop"""
    print("="*60)
    print("WAITING FOR VEO 3 TO BE READY")
    print("="*60)
    print("Checking every 5 minutes...")
    print("Will start posting 8-second videos when Veo 3 is working")
    print("="*60)
    
    while True:
        if check_veo3_ready():
            start_automation_when_ready()
            break
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting 5 minutes before next check...")
            time.sleep(300)  # Wait 5 minutes

if __name__ == "__main__":
    main()



