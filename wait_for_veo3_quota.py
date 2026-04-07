#!/usr/bin/env python3
"""
Wait for Veo 3 quota to reset - checks every 30 minutes
"""

import time
from datetime import datetime
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

def check_veo3_quota():
    """Check if Veo 3 quota is available"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Veo 3 quota...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test with a very simple prompt
        test_prompt = "A red ball bouncing"
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                negative_prompt="blurry",
            ),
        )
        
        # If we get here without quota error, it's working
        print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS! Veo 3 quota available!")
        return True
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Quota exceeded, waiting for reset...")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False

def start_automation_when_ready():
    """Start the main automation once Veo 3 quota is available"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Veo 3 quota available! Starting full automation...")
    
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
    print("WAITING FOR VEO 3 QUOTA TO RESET")
    print("="*60)
    print("Checking every 30 minutes...")
    print("Will start posting 8-second videos when quota is available")
    print("="*60)
    
    while True:
        if check_veo3_quota():
            start_automation_when_ready()
            break
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting 30 minutes before next check...")
            time.sleep(1800)  # Wait 30 minutes

if __name__ == "__main__":
    main()



