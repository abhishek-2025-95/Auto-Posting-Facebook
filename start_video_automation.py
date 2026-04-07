#!/usr/bin/env python3
"""
Start the video-only automation system
"""

import time
from datetime import datetime

def start_video_automation():
    print("="*60)
    print("STARTING VIDEO-ONLY AUTOMATION SYSTEM")
    print("="*60)
    print("System: Video + Caption + Hashtags")
    print("Frequency: 10 times per day (every 2.4 hours)")
    print("Target: US breaking news only")
    print("="*60)
    
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("The system will automatically retry when Veo 3 quotas reset.")
    print("Press Ctrl+C to stop the system.")
    print("="*60)
    
    try:
        # Import and run the main automation
        from main import main
        main()
    except KeyboardInterrupt:
        print("\nSystem stopped by user.")
    except Exception as e:
        print(f"System error: {e}")
        print("The system will continue running and retry automatically.")

if __name__ == "__main__":
    start_video_automation()



