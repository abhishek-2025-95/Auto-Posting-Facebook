#!/usr/bin/env python3
"""
Monitor paid billing activation - checks every 5 minutes
"""

import time
from datetime import datetime
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

def check_paid_billing_ready():
    """Check if paid billing is fully activated"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking paid billing activation...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test Veo 3 with a simple prompt
        test_prompt = "A red ball bouncing"
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                negative_prompt="blurry",
            ),
        )
        
        # If we get here without quota error, paid billing is working
        print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS! Paid billing fully activated!")
        print("Veo 3 is now working with your credits!")
        return True
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Still waiting for billing propagation...")
        elif "billed users" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Still waiting for billing activation...")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False

def start_automation_when_ready():
    """Start the main automation once paid billing is fully active"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Paid billing active! Starting full automation...")
    
    # Import and run the main automation
    from main import run_automation_cycle
    run_automation_cycle()
    
    # Schedule regular posts
    import schedule
    schedule.every(288).minutes.do(run_automation_cycle)  # Every 4.8 hours (5 times per day)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Full automation started! Will post 5 times per day with 8-second Veo 3 videos.")

def main():
    """Main monitoring loop"""
    print("="*60)
    print("MONITORING PAID BILLING ACTIVATION")
    print("="*60)
    print("Your account is paid - waiting for API propagation...")
    print("Checking every 5 minutes...")
    print("Will start posting 8-second videos when ready")
    print("="*60)
    
    while True:
        if check_paid_billing_ready():
            start_automation_when_ready()
            break
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting 5 minutes before next check...")
            time.sleep(300)  # Wait 5 minutes

if __name__ == "__main__":
    main()



