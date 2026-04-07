#!/usr/bin/env python3
"""
Monetization-Optimized Posting Schedule for Maximum USA Reach
Based on peak engagement times and monetization-friendly content strategy
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
from facebook_api import post_to_facebook_page, post_text_only, test_facebook_connection
from config import POSTS_PER_DAY, MINUTES_BETWEEN_POSTS
from enhanced_news_diversity import get_fresh_viral_news, save_posted_article

# Monetization-optimized posting schedule for USA
MONETIZATION_SCHEDULE = {
    # Peak engagement times in USA (EST/PST optimized)
    "morning_rush": "07:00",      # East Coast morning commute
    "mid_morning": "10:30",       # Peak work break time
    "lunch_break": "12:30",       # Lunch break engagement
    "afternoon_peak": "15:00",    # Afternoon work break
    "evening_commute": "17:30",    # East Coast evening commute
    "prime_time": "20:00",        # Prime time viewing
    "late_evening": "22:00",       # West Coast prime time
    "night_owl": "23:30",          # Late night engagement
    "early_riser": "06:00",        # Early morning news
    "weekend_peak": "11:00"        # Weekend morning engagement
}

# Content categories for monetization optimization
MONETIZATION_CATEGORIES = {
    "high_engagement": ["politics", "scandal", "crisis", "breaking"],
    "viral_potential": ["trending", "shocking", "exclusive", "urgent"],
    "monetization_friendly": ["economy", "business", "technology", "health"],
    "shareable_content": ["controversy", "outrage", "drama", "conflict"]
}

def get_optimal_posting_times():
    """
    Get optimal posting times for maximum USA reach and monetization
    OPTIMIZED FOR US AUDIENCE - IST times that hit US prime hours
    """
    current_time = datetime.now()
    day_of_week = current_time.strftime('%A')
    
    # Weekend vs weekday optimization
    if day_of_week in ['Saturday', 'Sunday']:
        return {
            "17:30": "8:00 AM EST - Weekend morning engagement",
            "20:00": "10:30 AM EST - Weekend mid-morning",
            "22:30": "1:00 PM EST - Weekend lunch time",
            "01:00": "3:30 PM EST - Weekend afternoon",
            "03:30": "6:00 PM EST - Weekend evening start",
            "05:00": "7:30 PM EST - Weekend prime time",
            "06:30": "9:00 PM EST - Weekend prime time",
            "08:00": "10:30 PM EST - Weekend late prime"
        }
    else:
        return {
            "17:30": "8:00 AM EST - Morning commute (East Coast)",
            "20:00": "10:30 AM EST - Work hours peak",
            "22:30": "1:00 PM EST - Lunch break engagement",
            "01:00": "3:30 PM EST - Afternoon work break",
            "03:30": "6:00 PM EST - Evening commute start",
            "05:00": "7:30 PM EST - Evening prime time",
            "06:30": "9:00 PM EST - Prime time viewing",
            "08:00": "10:30 PM EST - West Coast prime time",
            "09:30": "12:00 AM EST - Late prime time",
            "11:00": "1:30 AM EST - Late night engagement"
        }

def select_monetization_optimized_topic(article_list):
    """
    Select topics that are most likely to generate revenue and engagement
    """
    print("Selecting monetization-optimized viral topic...")
    
    # Score articles based on monetization potential
    scored_articles = []
    
    for article in article_list:
        score = 0
        title_lower = article['title'].lower()
        desc_lower = article['description'].lower()
        
        # High engagement keywords (more views = more ad revenue)
        high_engagement_keywords = ["breaking", "exclusive", "shocking", "crisis", "scandal", "urgent"]
        for keyword in high_engagement_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score += 3
        
        # Monetization-friendly topics (better for ads)
        monetization_keywords = ["economy", "business", "technology", "health", "finance", "market"]
        for keyword in monetization_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score += 2
        
        # Viral potential keywords (more shares = more reach)
        viral_keywords = ["trending", "viral", "outrage", "controversy", "drama"]
        for keyword in viral_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score += 2
        
        # Political content (high engagement but be careful)
        political_keywords = ["election", "politics", "government", "congress", "senate"]
        for keyword in political_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score += 1  # Moderate boost for political content
        
        scored_articles.append({
            **article,
            'monetization_score': score
        })
    
    # Sort by monetization score (highest first)
    scored_articles.sort(key=lambda x: x['monetization_score'], reverse=True)
    
    if scored_articles:
        selected = scored_articles[0]
        print(f"Selected: {selected['title']}")
        print(f"Monetization Score: {selected['monetization_score']}")
        return selected
    
    return None

def generate_monetization_optimized_caption(article):
    """
    Generate captions optimized for monetization and engagement
    """
    print("Generating monetization-optimized caption...")
    
    # Enhanced caption with monetization-friendly elements
    enhanced_prompt = f"""
    Create a Facebook caption for this breaking news that maximizes engagement and monetization potential:

    NEWS: {article['title']}
    DESCRIPTION: {article['description']}

    Requirements for maximum monetization:
    1. Start with high-engagement hook (question, shocking statement, or "BREAKING")
    2. Include emotional triggers (urgency, curiosity, outrage)
    3. Add call-to-action for engagement ("What do you think?", "Share your thoughts")
    4. Include relevant hashtags for reach (#BreakingNews #USNews #Trending)
    5. Keep it under 200 characters for better engagement
    6. Make it shareable and comment-worthy
    7. Avoid controversial political statements that might hurt monetization

    Focus on engagement metrics that drive ad revenue:
    - Comments and shares
    - Time spent on post
    - Click-through rates
    - Video completion rates

    Output: A single, highly engaging caption optimized for monetization.
    """
    
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(enhanced_prompt)
        
        caption = response.text.strip()
        
        # Ensure hashtags are included
        if not any(tag in caption for tag in ['#BreakingNews', '#USNews', '#Trending']):
            caption += "\n\n#BreakingNews #USNews #Trending"
        
        print("Monetization-optimized caption generated")
        return caption
        
    except Exception as e:
        print(f"Error generating monetization caption: {e}")
        # Fallback to regular caption generation
        return generate_facebook_caption(article)

def setup_monetization_optimized_schedule():
    """
    Setup posting schedule optimized for maximum USA reach and monetization
    """
    print("Setting up MONETIZATION-OPTIMIZED schedule...")
    print("Target: Maximum USA reach + Easy monetization")
    print("="*60)
    
    # Get optimal times for current day
    optimal_times = get_optimal_posting_times()
    
    print("Optimal posting times for maximum reach:")
    for time_str, description in optimal_times.items():
        print(f"   {time_str} - {description}")
    
    # Schedule posts at optimal times
    for time_str in optimal_times.keys():
        schedule.every().day.at(time_str).do(run_monetization_cycle)
        print(f"Scheduled: {time_str} - {optimal_times[time_str]}")
    
    # Also keep the interval-based posting as backup
    schedule.every(144).minutes.do(run_monetization_cycle)
    print("Backup interval: Every 144 minutes")

def check_veo3_quota():
    """Check if Veo 3 quota is available for video generation"""
    try:
        from check_veo3_status import check_veo3_quota
        return check_veo3_quota()
    except:
        # If check fails, assume quota is available
        return True

def run_monetization_cycle():
    """
    Enhanced automation cycle optimized for monetization and maximum reach
    """
    print("\n" + "="*60)
    print(f"MONETIZATION-OPTIMIZED CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: Maximum USA reach + Easy monetization")
    print("="*60)
    
    # Check Veo 3 quota before starting
    if not check_veo3_quota():
        print("Veo 3 quota exceeded - skipping this cycle")
        print("Will retry when quota resets")
        return False
    
    try:
        # Step 1: Get fresh viral news (avoiding repeats)
        print("\nStep 1: Fetching FRESH viral news...")
        viral_article = get_fresh_viral_news()
        
        if not viral_article:
            print("No fresh articles found, skipping this cycle")
            return False
        
        print(f"Selected FRESH content: {viral_article['title']}")
        
        # Step 2: Generate monetization-optimized caption
        print("\nStep 2: Generating monetization-optimized caption...")
        caption = generate_monetization_optimized_caption(viral_article)
        
        if not caption:
            print("No caption generated, skipping this cycle")
            return False
        
        print("Monetization-optimized caption generated")
        
        # Step 4: Generate video (REQUIRED - no text-only fallback)
        print("\nStep 4: Generating post video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("VIDEO GENERATION FAILED - This page is video-only")
            print("Skipping this cycle. Will retry when Veo 3 quota resets.")
            print("No text-only posts will be created.")
            return False
        
        print("Video generated successfully")
        
        # Step 5: Verify monetization components
        print("\nStep 5: Verifying monetization components...")
        print(f"Video: {video_file} ({os.path.getsize(video_file)} bytes)")
        print(f"Caption: {len(caption)} characters")
        print(f"Engagement hooks: {'?' in caption or '!' in caption}")
        print(f"Hashtags: {'#BreakingNews' in caption and '#USNews' in caption}")
        
        # Step 6: Post to Facebook
        print("\nStep 6: Posting monetization-optimized content to Facebook...")
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up video file
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up video file: {video_file}")
        except:
            pass
        
        if success:
            print("\nMONETIZATION-OPTIMIZED POST SUCCESSFUL!")
            print("Optimized for maximum USA reach and ad revenue")
            save_posted_article(viral_article)  # prevent duplicate posts
            log_monetization_success(viral_article, caption)
        else:
            print("\nPOST FAILED! Will try again next cycle...")
            log_failure(viral_article)
        
        return success
        
    except Exception as e:
        print(f"\nCRITICAL ERROR in monetization cycle: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        log_error(e)
        return False

def log_monetization_success(article, caption):
    """Log successful monetization-optimized posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] MONETIZATION SUCCESS - {article['title']}\n"
    
    with open('monetization_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_failure(article):
    """Log failed posts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] FAILED - {article['title']}\n"
    
    with open('monetization_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_error(error):
    """Log critical errors"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] ERROR - {str(error)}\n"
    
    with open('monetization_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)

def check_requirements():
    """Check if all requirements are met"""
    print("Checking monetization system requirements...")
    
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
    
    print("All monetization requirements met!")
    return True

def main():
    """Main function for monetization-optimized automation"""
    print("MONETIZATION-OPTIMIZED AUTOMATION SYSTEM")
    print("="*60)
    print("Target: Maximum USA reach + Easy monetization")
    print("Schedule: Peak engagement times")
    print("Content: Monetization-friendly topics")
    print("Automation: 10 posts per day")
    print("="*60)
    
    # Check requirements
    if not check_requirements():
        print("\nSystem requirements not met. Please fix the issues above.")
        return
    
    # Setup monetization-optimized schedule
    setup_monetization_optimized_schedule()
    
    # Run initial cycle
    print("\nRunning initial monetization-optimized cycle...")
    run_monetization_cycle()
    
    # Main loop
    print(f"\nStarting monetization scheduler...")
    print("Press Ctrl+C to stop the system")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nMonetization system stopped by user")
        print("Check monetization_log.txt for activity history")

if __name__ == "__main__":
    main()

