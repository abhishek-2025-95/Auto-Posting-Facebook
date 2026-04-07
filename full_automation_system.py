#!/usr/bin/env python3
"""
Full Automation System - Scheduled Posting
Automatically posts 10 times per day at peak engagement times
"""

import schedule
import time
from datetime import datetime
import os

def run_automation_cycle():
    """Main automation cycle with video retry logic"""
    print("\n" + "="*50)
    print(f"AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        # Step 1: Get trending news
        print("\nStep 1: Fetching trending news...")
        from news_fetcher import get_trending_news, select_viral_topic
        
        article_list = get_trending_news()
        if not article_list:
            print("No articles found, skipping this cycle")
            return False
        
        print(f"Found {len(article_list)} articles")
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(article_list)
        if not viral_article:
            print("No viral article selected, skipping this cycle")
            return False
        
        print(f"Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating caption...")
        from content_generator import generate_facebook_caption
        
        caption = generate_facebook_caption(viral_article)
        if not caption:
            print("No caption generated, skipping this cycle")
            return False
        
        print("Caption generated successfully")
        
        # Step 4: Generate video with retry logic
        print("\nStep 4: Generating video...")
        from content_generator import generate_post_video
        
        video_file = None
        max_retries = 3
        
        for attempt in range(max_retries):
            print(f"Video generation attempt {attempt + 1}/{max_retries}...")
            print("Generating video (this may take 2-3 minutes)...")
            
            video_file = generate_post_video(viral_article)
            
            if video_file and os.path.exists(video_file):
                print(f"SUCCESS: Video generated - {video_file}")
                break
            else:
                print(f"Attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    print("Waiting 30 seconds before retry...")
                    time.sleep(30)
                else:
                    print("All video generation attempts failed")
                    print("NO POST WITHOUT VIDEO - Skipping this cycle")
                    return False
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed - NO POST WITHOUT VIDEO")
            return False
        
        # Step 5: Post video to Facebook
        print("\nStep 5: Posting video to Facebook...")
        from facebook_api import post_to_facebook_page
        
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up video file
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up video file: {video_file}")
        except:
            pass
        
        if success:
            print("\nPOST SUCCESSFUL!")
            log_success(viral_article, caption)
            return True
        else:
            print("\nPOST FAILED!")
            log_failure(viral_article)
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        log_error(e)
        return False

def log_success(article, caption):
    """Log successful posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] SUCCESS - {article['title']}\n"
    
    with open('automation_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_failure(article):
    """Log failed posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] FAILED - {article['title']}\n"
    
    with open('automation_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_error(error):
    """Log critical errors"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] ERROR - {str(error)}\n"
    
    with open('automation_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def setup_schedule():
    """Setup the posting schedule for maximum USA reach"""
    print("Setting up automation schedule...")
    print("Peak engagement times for USA:")
    
    # Peak engagement times for USA
    schedule.every().day.at("07:00").do(run_automation_cycle)  # Morning commute
    schedule.every().day.at("10:30").do(run_automation_cycle)  # Work break
    schedule.every().day.at("12:30").do(run_automation_cycle)  # Lunch break
    schedule.every().day.at("15:00").do(run_automation_cycle)  # Afternoon break
    schedule.every().day.at("17:30").do(run_automation_cycle)  # Evening commute
    schedule.every().day.at("20:00").do(run_automation_cycle)  # Prime time
    schedule.every().day.at("22:00").do(run_automation_cycle)  # West Coast prime
    schedule.every().day.at("23:30").do(run_automation_cycle)  # Late night
    
    # Also schedule interval-based posting (every 144 minutes)
    schedule.every(144).minutes.do(run_automation_cycle)
    
    print("Schedule set up successfully!")
    print("Posts will be made at:")
    print("07:00, 10:30, 12:30, 15:00, 17:30, 20:00, 22:00, 23:30")
    print("Plus every 144 minutes between scheduled times")

def check_requirements():
    """Check if all requirements are met"""
    print("Checking system requirements...")
    
    try:
        from facebook_api import test_facebook_connection
        if test_facebook_connection():
            print("Facebook connection: SUCCESS")
        else:
            print("Facebook connection: FAILED")
            return False
    except Exception as e:
        print(f"Facebook connection error: {e}")
        return False
    
    print("All requirements met!")
    return True

def show_next_posts():
    """Show when the next posts will be made"""
    print("\nNEXT POSTING SCHEDULE:")
    print("="*40)
    
    current_time = datetime.now()
    day_of_week = current_time.strftime('%A')
    
    peak_times = [
        "07:00 - Morning commute (East Coast)",
        "10:30 - Work break peak",
        "12:30 - Lunch break",
        "15:00 - Afternoon break",
        "17:30 - Evening commute",
        "20:00 - Prime time viewing",
        "22:00 - West Coast prime",
        "23:30 - Late night engagement"
    ]
    
    print(f"Today ({day_of_week}):")
    for time_str in peak_times:
        print(f"  {time_str}")
    
    print(f"\nInterval posting: Every 144 minutes")
    print(f"Total posts per day: 10")

def main():
    """Main function"""
    print("FULL AUTOMATION SYSTEM")
    print("="*50)
    print("Automated posting: 10 times per day")
    print("Peak engagement times for USA")
    print("Video posts only (no text posts)")
    print("="*50)
    
    # Show next posting schedule
    show_next_posts()
    
    # Check requirements
    if not check_requirements():
        print("\nSystem requirements not met. Please fix the issues above.")
        return
    
    # Setup schedule
    setup_schedule()
    
    # Run initial cycle
    print("\nRunning initial automation cycle...")
    run_automation_cycle()
    
    # Main loop
    print(f"\nStarting automation scheduler...")
    print("System will automatically post at scheduled times")
    print("Press Ctrl+C to stop the system")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
        print("Check automation_log.txt for activity history")

if __name__ == "__main__":
    main()


