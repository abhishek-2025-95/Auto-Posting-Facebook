#!/usr/bin/env python3
"""
Token-Managed Automation System
Automatically handles Facebook token refresh and validation
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
from token_manager import FacebookTokenManager
from enhanced_config import (
    POSTS_PER_DAY, MINUTES_BETWEEN_POSTS, 
    TOKEN_REFRESH_DAYS_BEFORE_EXPIRY, TOKEN_VALIDATION_INTERVAL_HOURS,
    AUTOMATIC_TOKEN_REFRESH, TOKEN_MONITORING_ENABLED
)

class TokenManagedAutomation:
    def __init__(self):
        self.token_manager = FacebookTokenManager()
        self.last_token_check = None
        self.token_health_status = True
        
    def check_token_health(self):
        """Check token health before each cycle"""
        if not TOKEN_MONITORING_ENABLED:
            return True
            
        print("🔍 Checking token health...")
        
        # Check if we need to validate token
        if (self.last_token_check is None or 
            datetime.now() - self.last_token_check > timedelta(hours=TOKEN_VALIDATION_INTERVAL_HOURS)):
            
            print("🔄 Performing token health check...")
            self.token_health_status = self.token_manager.monitor_token_health()
            self.last_token_check = datetime.now()
            
            if not self.token_health_status:
                print("⚠️ Token health check failed!")
                if AUTOMATIC_TOKEN_REFRESH:
                    print("🔄 Attempting automatic token refresh...")
                    new_token = self.token_manager.refresh_token_automatically()
                    if new_token:
                        print("✅ Token refreshed successfully!")
                        self.token_health_status = True
                    else:
                        print("❌ Automatic refresh failed - manual intervention required")
                        return False
                else:
                    print("❌ Automatic refresh disabled - manual intervention required")
                    return False
        
        return self.token_health_status
    
    def run_automation_cycle(self):
        """Enhanced automation cycle with token management"""
        print("\n" + "="*60)
        print(f"🚀 TOKEN-MANAGED AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            # Step 0: Check token health
            print("\n🔍 Step 0: Checking token health...")
            if not self.check_token_health():
                print("❌ Token health check failed, skipping this cycle")
                return False
            
            print("✅ Token health check passed")
            
            # Step 1: Get trending news
            print("\n📰 Step 1: Fetching trending news...")
            article_list = get_trending_news()
            
            if not article_list:
                print("❌ No articles found, skipping this cycle")
                return False
            
            # Step 2: Select viral topic
            print("\n🎯 Step 2: Selecting viral topic...")
            viral_article = select_viral_topic(article_list)
            
            if not viral_article:
                print("❌ No viral article selected, skipping this cycle")
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
                return False
            
            print("✅ Video generated successfully")
            
            # Step 5: Verify all three components before posting
            print("\n🔍 Step 5: Verifying post components...")
            print(f"✅ Video: {video_file} ({os.path.getsize(video_file)} bytes)")
            print(f"✅ Caption: {len(caption)} characters")
            print(f"✅ Hashtags: {'#BreakingNews' in caption and '#USNews' in caption}")
            
            # Step 6: Post to Facebook (with token validation)
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
                print("\n🎉 POST SUCCESSFUL! Token management working correctly.")
                self.log_success(viral_article, caption)
            else:
                print("\n❌ POST FAILED! Will try again next cycle...")
                self.log_failure(viral_article)
            
            return success
            
        except Exception as e:
            print(f"\n💥 CRITICAL ERROR in automation cycle: {e}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            self.log_error(e)
            return False
    
    def log_success(self, article, caption):
        """Log successful posts"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] SUCCESS - {article['title']}\n"
        
        with open('token_managed_log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_failure(self, article):
        """Log failed posts"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] FAILED - {article['title']}\n"
        
        with open('token_managed_log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_error(self, error):
        """Log critical errors"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] ERROR - {str(error)}\n"
        
        with open('token_managed_log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def setup_schedule(self):
        """Setup the posting schedule with token management"""
        print(f"⏰ Setting up TOKEN-MANAGED schedule: {POSTS_PER_DAY} posts per day")
        print(f"⏱️ Interval: Every {MINUTES_BETWEEN_POSTS} minutes")
        print(f"🔍 Token monitoring: {'ENABLED' if TOKEN_MONITORING_ENABLED else 'DISABLED'}")
        print(f"🔄 Automatic refresh: {'ENABLED' if AUTOMATIC_TOKEN_REFRESH else 'DISABLED'}")
        
        # Schedule the automation cycle
        schedule.every(MINUTES_BETWEEN_POSTS).minutes.do(self.run_automation_cycle)
        
        # Also schedule at specific times for better distribution
        schedule.every().day.at("06:00").do(self.run_automation_cycle)  # 6 AM
        schedule.every().day.at("10:30").do(self.run_automation_cycle)  # 10:30 AM
        schedule.every().day.at("15:00").do(self.run_automation_cycle)  # 3 PM
        schedule.every().day.at("19:30").do(self.run_automation_cycle)  # 7:30 PM
        schedule.every().day.at("22:00").do(self.run_automation_cycle)  # 10 PM
        
        # Schedule token health checks
        if TOKEN_MONITORING_ENABLED:
            schedule.every().day.at("02:00").do(self.check_token_health)  # Daily token check
    
    def check_requirements(self):
        """Check if all requirements are met"""
        print("Checking token-managed system requirements...")
        
        # Check config file
        try:
            from enhanced_config import GEMINI_API_KEY, NEWS_API_KEY, FACEBOOK_ACCESS_TOKEN
            if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
                print("Please set your GEMINI_API_KEY in enhanced_config.py")
                return False
            if NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
                print("Please set your NEWS_API_KEY in enhanced_config.py")
                return False
            if FACEBOOK_ACCESS_TOKEN == "YOUR_FACEBOOK_ACCESS_TOKEN_HERE":
                print("Please set your FACEBOOK_ACCESS_TOKEN in enhanced_config.py")
                return False
        except ImportError:
            print("enhanced_config.py not found or invalid")
            return False
        
        # Test Facebook connection
        if not test_facebook_connection():
            print("Facebook API connection failed")
            return False
        
        # Test token manager
        print("Testing token manager...")
        if not self.token_manager.validate_token(self.token_manager.current_token):
            print("❌ Current token is invalid")
            return False
        
        print("✅ All token-managed requirements met!")
        return True
    
    def show_token_status(self):
        """Show current token status"""
        print("\n🔍 TOKEN STATUS REPORT")
        print("="*40)
        
        # Validate token
        is_valid = self.token_manager.validate_token(self.token_manager.current_token)
        print(f"Token Valid: {'✅ YES' if is_valid else '❌ NO'}")
        
        # Get token info
        token_info = self.token_manager.get_token_info(self.token_manager.current_token)
        if token_info:
            print(f"Token Type: {token_info.get('type', 'Unknown')}")
            print(f"Scopes: {', '.join(token_info.get('scopes', []))}")
        
        # Check expiry
        is_expired, message = self.token_manager.check_token_expiry(self.token_manager.current_token)
        print(f"Expiry Status: {message}")
        
        # Token health
        print(f"Token Health: {'✅ HEALTHY' if self.token_health_status else '❌ UNHEALTHY'}")
        
        print("="*40)
    
    def main(self):
        """Main function for token-managed automation"""
        print("🔐 TOKEN-MANAGED AUTOMATION SYSTEM")
        print("="*60)
        print("Automated posting: 10 times per day")
        print("Target: US breaking news videos only")
        print("Components: Video + Caption + Hashtags")
        print("NEW: Automatic token management and refresh")
        print("="*60)
        
        # Show token status
        self.show_token_status()
        
        # Check requirements
        if not self.check_requirements():
            print("\nSystem requirements not met. Please fix the issues above.")
            return
        
        # Setup schedule
        self.setup_schedule()
        
        # Run initial cycle
        print("\n🚀 Running initial token-managed automation cycle...")
        self.run_automation_cycle()
        
        # Main loop
        print(f"\n⏰ Starting token-managed scheduler...")
        print("Press Ctrl+C to stop the system")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n🛑 Token-managed system stopped by user")
            print("📊 Check token_managed_log.txt for activity history")

if __name__ == "__main__":
    automation = TokenManagedAutomation()
    automation.main()


