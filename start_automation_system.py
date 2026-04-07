#!/usr/bin/env python3
"""
Start Automation System - Simplified Version
Monetization-optimized Facebook automation without Unicode characters
"""

import schedule
import time
import traceback
import json
from datetime import datetime, timedelta
import os

# Import our modules
from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page, test_facebook_connection
from config import POSTS_PER_DAY, MINUTES_BETWEEN_POSTS

def run_automation_cycle():
    """
    Main automation cycle - monetization optimized
    """
    print("\n" + "="*60)
    print(f"AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Step 1: Get trending news
        print("\nStep 1: Fetching trending news...")
        article_list = get_trending_news()
        
        if not article_list:
            print("No articles found, skipping this cycle")
            return False
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(article_list)
        
        if not viral_article:
            print("No viral article selected, skipping this cycle")
            return False
        
        print(f"Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating Facebook caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("No caption generated, skipping this cycle")
            return False
        
        print("Caption generated successfully")
        
        # Step 4: Generate video
        print("\nStep 4: Generating post video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed - skipping this cycle")
            return False
        
        print("Video generated successfully")
        
        # Step 5: Post to Facebook
        print("\nStep 5: Posting to Facebook...")
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
        else:
            print("\nPOST FAILED!")
            log_failure(viral_article)
        
        return success
        
    except Exception as e:
        print(f"\nERROR in automation cycle: {e}")
        print(f"Traceback: {traceback.format_exc()}")
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
    print(f"Setting up schedule: {POSTS_PER_DAY} posts per day")
    print(f"Interval: Every {MINUTES_BETWEEN_POSTS} minutes")
    
    # Peak engagement times for USA
    schedule.every().day.at("07:00").do(run_automation_cycle)  # Morning commute
    schedule.every().day.at("10:30").do(run_automation_cycle)  # Work break
    schedule.every().day.at("12:30").do(run_automation_cycle)  # Lunch break
    schedule.every().day.at("15:00").do(run_automation_cycle)  # Afternoon break
    schedule.every().day.at("17:30").do(run_automation_cycle)  # Evening commute
    schedule.every().day.at("20:00").do(run_automation_cycle)  # Prime time
    schedule.every().day.at("22:00").do(run_automation_cycle)  # West Coast prime
    schedule.every().day.at("23:30").do(run_automation_cycle)  # Late night
    
    # Also schedule interval-based posting
    schedule.every(MINUTES_BETWEEN_POSTS).minutes.do(run_automation_cycle)

def check_requirements():
    """Check if all requirements are met"""
    print("Checking system requirements...")
    
    # Check config file
    try:
        from config import GEMINI_API_KEY, NEWS_API_KEY, FACEBOOK_ACCESS_TOKEN
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            print("Please set your GEMINI_API_KEY in config.py")
            return False
        if NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
            print("Please set your NEWS_API_KEY in config.py")
            return False
        if FACEBOOK_ACCESS_TOKEN == "YOUR_FACEBOOK_ACCESS_TOKEN_HERE":
            print("Please set your FACEBOOK_ACCESS_TOKEN in config.py")
            return False
    except ImportError:
        print("config.py not found or invalid")
        return False
    
    # Test Facebook connection
    if not test_facebook_connection():
        print("Facebook API connection failed")
        return False
    
    print("All requirements met!")
    return True

def show_next_posts():
    """Show when the next posts will be made"""
    print("\nNEXT POSTING SCHEDULE:")
    print("="*40)
    
    current_time = datetime.now()
    day_of_week = current_time.strftime('%A')
    
    # Peak times for USA
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
    
    print(f"\nInterval posting: Every {MINUTES_BETWEEN_POSTS} minutes")
    print(f"Total posts per day: {POSTS_PER_DAY}")

def main():
    """Main function"""
    print("MONETIZATION-OPTIMIZED AUTOMATION SYSTEM")
    print("="*60)
    print("Target: Maximum USA reach + Easy monetization")
    print("Schedule: Peak engagement times")
    print("Content: Monetization-friendly topics")
    print("Automation: 10 posts per day")
    print("="*60)
    
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
    print(f"\nStarting scheduler...")
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


