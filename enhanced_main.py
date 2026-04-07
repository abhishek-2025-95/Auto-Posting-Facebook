# enhanced_main.py - Enhanced automation with article diversity tracking
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

# Global tracking for posted articles
POSTED_ARTICLES_FILE = "posted_articles.json"
MAX_DAILY_POSTS = 10

def load_posted_articles():
    """Load previously posted articles to avoid duplicates"""
    if os.path.exists(POSTED_ARTICLES_FILE):
        try:
            with open(POSTED_ARTICLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('posted_articles', [])
        except:
            return []
    return []

def save_posted_article(article):
    """Save posted article to avoid reposting"""
    posted_articles = load_posted_articles()
    
    # Add new article
    posted_articles.append({
        'title': article['title'],
        'url': article['url'],
        'posted_at': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d')
    })
    
    # Keep only last 7 days of articles
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    posted_articles = [a for a in posted_articles if a['date'] >= cutoff_date]
    
    # Save to file
    data = {
        'posted_articles': posted_articles,
        'last_updated': datetime.now().isoformat()
    }
    
    with open(POSTED_ARTICLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_article_already_posted(article, posted_articles):
    """Check if article was already posted today"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    for posted in posted_articles:
        if posted['date'] == today:
            # Check for similar titles (avoid exact duplicates)
            if (article['title'].lower().strip() == posted['title'].lower().strip() or
                article['url'] == posted['url']):
                return True
    return False

def get_daily_post_count(posted_articles):
    """Get count of posts made today"""
    today = datetime.now().strftime('%Y-%m-%d')
    return len([a for a in posted_articles if a['date'] == today])

def select_unique_viral_topic(article_list):
    """Select a viral topic that hasn't been posted today"""
    posted_articles = load_posted_articles()
    daily_count = get_daily_post_count(posted_articles)
    
    print(f"📊 Daily posts so far: {daily_count}/{MAX_DAILY_POSTS}")
    
    if daily_count >= MAX_DAILY_POSTS:
        print("❌ Daily post limit reached (10 posts)")
        return None
    
    # Filter out already posted articles
    available_articles = []
    for article in article_list:
        if not is_article_already_posted(article, posted_articles):
            available_articles.append(article)
    
    if not available_articles:
        print("❌ No new articles available (all already posted today)")
        return None
    
    print(f"✅ Found {len(available_articles)} new articles to choose from")
    
    # Use the existing selection logic on filtered articles
    return select_viral_topic(available_articles)

def run_automation_cycle():
    """
    Enhanced automation cycle with article diversity tracking
    """
    print("\n" + "="*60)
    print(f"🚀 RUNNING ENHANCED AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Step 1: Get trending news
        print("\n📰 Step 1: Fetching trending news...")
        article_list = get_trending_news()
        
        if not article_list:
            print("❌ No articles found, skipping this cycle")
            return False
        
        # Step 2: Select unique viral topic (avoid duplicates)
        print("\n🎯 Step 2: Selecting unique viral topic...")
        viral_article = select_unique_viral_topic(article_list)
        
        if not viral_article:
            print("❌ No unique viral article available, skipping this cycle")
            return False
        
        print(f"✅ Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\n✍️ Step 3: Generating Facebook caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("❌ No caption generated, skipping this cycle")
            return False
        
        print("✅ Caption generated successfully")
        
        # Step 4: Generate video (REQUIRED - no fallback)
        print("\n🎬 Step 4: Generating post video...")
        video_file = generate_post_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("❌ VIDEO GENERATION FAILED - This page is video-only")
            print("Skipping this cycle. Will retry when Veo 3 quota resets.")
            print("Next attempt in 2.4 hours...")
            return False
        
        print("✅ Video generated successfully")
        
        # Step 5: Verify all three components before posting
        print("\n🔍 Step 5: Verifying post components...")
        print(f"✅ Video: {video_file} ({os.path.getsize(video_file)} bytes)")
        print(f"✅ Caption: {len(caption)} characters")
        print(f"✅ Hashtags: {'#BreakingNews' in caption and '#USNews' in caption}")
        
        # Step 6: Post to Facebook
        print("\n📱 Step 6: Posting video to Facebook...")
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up video file
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"🧹 Cleaned up video file: {video_file}")
        except:
            pass
        
        if success:
            print("\n🎉 POST SUCCESSFUL! Article saved to avoid duplicates.")
            save_posted_article(viral_article)
            log_success(viral_article, caption)
        else:
            print("\n❌ POST FAILED! Will try again next cycle...")
            log_failure(viral_article)
        
        return success
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR in automation cycle: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
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
    """Setup the posting schedule"""
    print(f"⏰ Setting up schedule: {POSTS_PER_DAY} posts per day")
    print(f"⏱️ Interval: Every {MINUTES_BETWEEN_POSTS} minutes")
    print("🔄 Enhanced with article diversity tracking")
    
    # Schedule the automation cycle
    schedule.every(MINUTES_BETWEEN_POSTS).minutes.do(run_automation_cycle)
    
    # Also schedule at specific times for better distribution
    schedule.every().day.at("06:00").do(run_automation_cycle)  # 6 AM
    schedule.every().day.at("10:30").do(run_automation_cycle)  # 10:30 AM
    schedule.every().day.at("15:00").do(run_automation_cycle)  # 3 PM
    schedule.every().day.at("19:30").do(run_automation_cycle)  # 7:30 PM
    schedule.every().day.at("22:00").do(run_automation_cycle)  # 10 PM

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

def show_daily_summary():
    """Show summary of today's posts"""
    posted_articles = load_posted_articles()
    today = datetime.now().strftime('%Y-%m-%d')
    today_posts = [a for a in posted_articles if a['date'] == today]
    
    print(f"\n📊 TODAY'S POSTING SUMMARY ({today})")
    print("="*50)
    print(f"Posts made: {len(today_posts)}/{MAX_DAILY_POSTS}")
    
    if today_posts:
        print("\nPosted articles:")
        for i, post in enumerate(today_posts, 1):
            print(f"{i}. {post['title']}")
    else:
        print("No posts made today yet.")

def main():
    """Main function"""
    print("ENHANCED VIDEO-ONLY BREAKING NEWS AUTOMATION SYSTEM")
    print("="*60)
    print("Automated posting: 10 times per day")
    print("Target: US breaking news videos only")
    print("Components: Video + Caption + Hashtags")
    print("NEW: Article diversity tracking - no duplicate posts!")
    print("="*60)
    
    # Show today's summary
    show_daily_summary()
    
    # Check requirements
    if not check_requirements():
        print("\nSystem requirements not met. Please fix the issues above.")
        return
    
    # Setup schedule
    setup_schedule()
    
    # Run initial cycle
    print("\n🚀 Running initial automation cycle...")
    run_automation_cycle()
    
    # Main loop
    print(f"\n⏰ Starting scheduler... Next run in {MINUTES_BETWEEN_POSTS} minutes")
    print("Press Ctrl+C to stop the system")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n🛑 System stopped by user")
        print("📊 Check automation_log.txt for activity history")
        print("📊 Check posted_articles.json for posted article tracking")

if __name__ == "__main__":
    main()


