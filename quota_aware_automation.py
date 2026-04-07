#!/usr/bin/env python3
"""
Quota-aware automation system that only posts when video generation is possible
"""

import schedule
import time
import traceback
import json
from datetime import datetime, timedelta
import os

# Import our modules
from enhanced_news_diversity import get_fresh_viral_news
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page, test_facebook_connection

def check_veo3_quota():
    """Check if Veo 3 quota is available"""
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try a simple test to check quota
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        
        return True
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            return False
        return True

def check_imagen4_quota():
    """Check if Imagen 4 quota is available"""
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try a simple test to check quota
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        
        return True
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            return False
        return True

def run_quota_aware_cycle():
    """
    Automation cycle that only runs when video generation is possible
    """
    print("\n" + "="*60)
    print(f"QUOTA-AWARE CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Video-only posting - no text fallback")
    print("="*60)
    
    # Check quotas for video or image generation
    print("Checking quotas...")
    veo3_available = check_veo3_quota()
    imagen4_available = check_imagen4_quota()
    
    if not veo3_available and not imagen4_available:
        print("Both Veo 3 and Imagen 4 quotas exceeded - skipping this cycle")
        print("Will retry when quota resets")
        return False
    
    if veo3_available:
        print("Veo 3 quota available - will try video generation first")
    if imagen4_available:
        print("Imagen 4 quota available - will use as fallback if needed")
    
    try:
        # Step 1: Get fresh viral news
        print("\nStep 1: Fetching FRESH viral news...")
        viral_article = get_fresh_viral_news()
        
        if not viral_article:
            print("No fresh articles found, skipping this cycle")
            return False
        
        print(f"Selected FRESH content: {viral_article['title']}")
        
        # Step 2: Generate caption
        print("\nStep 2: Generating caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("No caption generated, skipping this cycle")
            return False
        
        print("Caption generated successfully")
        
        # Step 3: Try video generation first, fallback to image
        print("\nStep 3: Attempting video generation...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("VIDEO GENERATION FAILED - Veo 3 quota exceeded")
            print("Falling back to Imagen 4 image generation...")
            
            # Try image generation as fallback
            try:
                from content_generator import generate_image_with_imagen4
                image_file = generate_image_with_imagen4(viral_article)
                
                if image_file and os.path.exists(image_file):
                    print("Image generated successfully with Imagen 4")
                    
                    # Post with image
                    print("\nStep 4: Posting with image...")
                    success = post_to_facebook_page(caption, image_file)
                    
                    # Clean up image file
                    try:
                        if os.path.exists(image_file):
                            os.remove(image_file)
                            print("Image file cleaned up")
                    except:
                        pass
                    
                    if success:
                        print("SUCCESS: Image post created!")
                        log_success(viral_article, caption)
                    else:
                        print("FAILED: Image post failed")
                        log_failure(viral_article)
                    
                    return success
                else:
                    print("IMAGE GENERATION FAILED - skipping this cycle")
                    return False
                    
            except Exception as e:
                print(f"IMAGE GENERATION ERROR: {e}")
                print("Skipping this cycle - no visual content available")
                return False
        else:
            print("Video generated successfully")
            
            # Step 4: Post with video
            print("\nStep 4: Posting with video...")
            success = post_to_facebook_page(caption, video_file)
        
        # Clean up video file
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print("Video file cleaned up")
        except:
            pass
        
        if success:
            print("SUCCESS: Video post created!")
            log_success(viral_article, caption)
        else:
            print("FAILED: Video post failed")
            log_failure(viral_article)
        
        return success
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def log_success(article, caption):
    """Log successful posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] SUCCESS - {article['title']}\n"
    
    with open('quota_aware_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_failure(article):
    """Log failed posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] FAILED - {article['title']}\n"
    
    with open('quota_aware_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def setup_quota_aware_schedule():
    """Setup schedule that respects quota limits"""
    print("Setting up QUOTA-AWARE schedule...")
    print("Video-only posting - no text fallback")
    print("="*60)
    
    # US-optimized schedule (IST times)
    schedule_times = [
        '17:30', '20:00', '22:30', '01:00', '03:30', 
        '05:00', '06:30', '08:00', '09:30', '11:00'
    ]
    
    print("Scheduled posting times:")
    for time_str in schedule_times:
        schedule.every().day.at(time_str).do(run_quota_aware_cycle)
        print(f"  {time_str} IST - Video-only post")
    
    # Backup interval
    schedule.every(144).minutes.do(run_quota_aware_cycle)
    print("Backup interval: Every 144 minutes")

def main():
    """Main function for quota-aware automation"""
    print("QUOTA-AWARE AUTOMATION SYSTEM")
    print("="*60)
    print("Video-only posting - no text fallback")
    print("Respects Veo 3 quota limits")
    print("="*60)
    
    # Test Facebook connection
    if not test_facebook_connection():
        print("Facebook connection failed")
        return
    
    # Setup quota-aware schedule
    setup_quota_aware_schedule()
    
    # Run initial cycle
    print("\nRunning initial quota-aware cycle...")
    run_quota_aware_cycle()
    
    # Main loop
    print(f"\nStarting quota-aware scheduler...")
    print("Press Ctrl+C to stop the system")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nQuota-aware system stopped by user")
        print("Check quota_aware_log.txt for activity history")

if __name__ == "__main__":
    main()