#!/usr/bin/env python3
"""
Monitor Veo 3 quota and start automation when available
"""

import time
from datetime import datetime
from google import genai as imagen_genai
from google.genai import types
from config import GEMINI_API_KEY

def check_veo3_quota():
    """Check if Veo 3 quota is available"""
    try:
        client = imagen_genai.Client(api_key=GEMINI_API_KEY)
        
        # Try a minimal video generation to test quota
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
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Veo 3 quota available!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Veo 3 quota exhausted - waiting...")
            return False
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Veo 3 error: {e}")
            return False

def monitor_and_start():
    """Monitor quota and start automation when available"""
    print("="*60)
    print("VEO 3 QUOTA MONITOR")
    print("="*60)
    print("Monitoring Veo 3 quota every 10 minutes...")
    print("Will start automation when quota is available")
    print("Press Ctrl+C to stop monitoring")
    print("="*60)
    
    while True:
        try:
            if check_veo3_quota():
                print("\n🚀 QUOTA AVAILABLE! Starting video automation...")
                print("="*60)
                
                # Start the main automation system
                from main import main
                main()
                break
            else:
                print("Waiting 10 minutes before next check...")
                time.sleep(600)  # Wait 10 minutes
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    monitor_and_start()



