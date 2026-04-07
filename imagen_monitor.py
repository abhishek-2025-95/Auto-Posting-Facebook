#!/usr/bin/env python3
"""
Imagen 4 Monitor - Checks if Imagen 4 is working every 5 minutes
Only starts posting when Imagen 4 is fully functional
"""

import time
import schedule
from datetime import datetime
from content_generator import generate_image_with_imagen4

def test_imagen4():
    """Test if Imagen 4 is working"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testing Imagen 4...")
    
    try:
        # Test with a simple prompt
        test_prompt = "A professional business meeting room with modern furniture"
        result = generate_image_with_imagen4(test_prompt)
        
        if result and "Error" not in str(result):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Imagen 4 is working!")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Image generated: {result}")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Imagen 4 still not working: {result}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Imagen 4 error: {e}")
        return False

def start_automation_when_ready():
    """Start the main automation once Imagen 4 is working"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Imagen 4 is ready! Starting full automation...")
    
    # Import and run the main automation
    from main import run_automation_cycle
    run_automation_cycle()
    
    # Schedule regular posts
    schedule.every(288).minutes.do(run_automation_cycle)  # Every 4.8 hours (5 times per day)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Full automation started! Will post 5 times per day.")

def main():
    """Main monitoring loop"""
    print("="*60)
    print("IMAGEN 4 MONITOR - Waiting for billing to activate")
    print("="*60)
    print("Checking every 5 minutes...")
    print("Will start posting only when Imagen 4 is working")
    print("="*60)
    
    # Check immediately
    if test_imagen4():
        start_automation_when_ready()
    else:
        # Schedule checks every 5 minutes
        schedule.every(5).minutes.do(check_and_start)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def check_and_start():
    """Check Imagen 4 and start automation if ready"""
    if test_imagen4():
        # Clear the 5-minute check schedule
        schedule.clear()
        start_automation_when_ready()

if __name__ == "__main__":
    main()
