#!/usr/bin/env python3
"""
Start Scheduler - Shows schedule and starts automation
"""

import schedule
import time
from datetime import datetime
import os

def run_automation_cycle():
    """Main automation cycle"""
    print(f"\nAUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from news_fetcher import get_trending_news, select_viral_topic
        from content_generator import generate_facebook_caption, generate_post_video
        from facebook_api import post_to_facebook_page
        
        # Get news
        article_list = get_trending_news()
        if not article_list:
            print("No articles found, skipping")
            return False
        
        # Select topic
        viral_article = select_viral_topic(article_list)
        if not viral_article:
            print("No viral article, skipping")
            return False
        
        print(f"Selected: {viral_article['title'][:50]}...")
        
        # Generate caption
        caption = generate_facebook_caption(viral_article)
        if not caption:
            print("No caption, skipping")
            return False
        
        # Generate video
        print("Generating video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed, skipping")
            return False
        
        # Post to Facebook
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
        except:
            pass
        
        if success:
            print("POST SUCCESSFUL!")
            return True
        else:
            print("POST FAILED!")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def setup_schedule():
    """Setup the posting schedule"""
    print("Setting up automation schedule...")
    
    # Peak engagement times for USA
    schedule.every().day.at("07:00").do(run_automation_cycle)
    schedule.every().day.at("10:30").do(run_automation_cycle)
    schedule.every().day.at("12:30").do(run_automation_cycle)
    schedule.every().day.at("15:00").do(run_automation_cycle)
    schedule.every().day.at("17:30").do(run_automation_cycle)
    schedule.every().day.at("20:00").do(run_automation_cycle)
    schedule.every().day.at("22:00").do(run_automation_cycle)
    schedule.every().day.at("23:30").do(run_automation_cycle)
    
    # Interval posting
    schedule.every(144).minutes.do(run_automation_cycle)
    
    print("Schedule set up successfully!")

def show_schedule():
    """Show the posting schedule"""
    print("\n" + "="*60)
    print("AUTOMATION SCHEDULE")
    print("="*60)
    print("Your system will automatically post at these times:")
    print()
    print("07:00 - Morning commute (East Coast)")
    print("10:30 - Work break peak")
    print("12:30 - Lunch break")
    print("15:00 - Afternoon break")
    print("17:30 - Evening commute")
    print("20:00 - Prime time viewing")
    print("22:00 - West Coast prime")
    print("23:30 - Late night engagement")
    print()
    print("Plus every 144 minutes between scheduled times")
    print("Total: 10 posts per day")
    print("="*60)

def main():
    """Main function"""
    print("FACEBOOK AUTOMATION SYSTEM")
    print("="*60)
    
    # Show schedule
    show_schedule()
    
    # Test Facebook connection
    print("\nTesting Facebook connection...")
    try:
        from facebook_api import test_facebook_connection
        if test_facebook_connection():
            print("Facebook connection: SUCCESS")
        else:
            print("Facebook connection: FAILED")
            return
    except Exception as e:
        print(f"Facebook connection error: {e}")
        return
    
    # Setup schedule
    setup_schedule()
    
    print("\n" + "="*60)
    print("AUTOMATION SYSTEM STARTED")
    print("="*60)
    print("Your system is now running and will automatically post")
    print("at the scheduled times above.")
    print()
    print("The system will:")
    print("- Fetch viral news from Reddit")
    print("- Select most viral topics")
    print("- Generate professional captions")
    print("- Create 8-second videos")
    print("- Post to Facebook at peak times")
    print()
    print("Press Ctrl+C to stop the system")
    print("="*60)
    
    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")

if __name__ == "__main__":
    main()


