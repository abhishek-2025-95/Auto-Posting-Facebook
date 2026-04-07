#!/usr/bin/env python3
"""
Create a working video post with simplified prompts
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption
from facebook_api import post_to_facebook_page
from google import genai
from config import GEMINI_API_KEY
import os
import time

def create_simple_video_prompt(article):
    """Create a simple, direct video prompt"""
    title = article['title']
    
    # Create a simple, direct prompt based on the news
    if 'doritos' in title.lower() and 'gun' in title.lower():
        return "An 8-second video showing a teenager with a bag of chips at a security scanner, with police officers nearby"
    elif 'ai' in title.lower():
        return "An 8-second video showing AI technology and security systems"
    elif 'teen' in title.lower():
        return "An 8-second video showing a teenager in a school or public setting"
    else:
        return "An 8-second video showing breaking news with dramatic lighting"

def generate_simple_video(article):
    """Generate video with simplified prompt"""
    print("Generating video with simplified prompt...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Create simple prompt
        simple_prompt = create_simple_video_prompt(article)
        print(f"Using simple prompt: {simple_prompt}")
        
        # Generate video
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=simple_prompt,
            config=genai.types.GenerateVideosConfig(
                negative_prompt="blurry, low quality, distorted",
            ),
        )
        
        print("Video generation started, waiting for completion...")
        
        # Wait for completion
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while not operation.done and wait_time < max_wait:
            print(f"Generating video... ({wait_time}s)")
            time.sleep(20)
            wait_time += 20
            operation = client.operations.get(operation)
        
        if operation.done and operation.result and operation.result.generated_videos:
            generated_video = operation.result.generated_videos[0]
            
            # Download and save the video
            video_path = "working_video.mp4"
            client.files.download(file=generated_video.video)
            generated_video.video.save(video_path)
            
            print(f"SUCCESS: Video saved as {video_path}")
            return video_path
        else:
            print("No video generated")
            return None
            
    except Exception as e:
        print(f"Error generating video: {e}")
        return None

def create_working_video_post():
    """Create a working video post"""
    print("="*60)
    print("CREATING WORKING VIDEO POST")
    print("="*60)
    
    try:
        # Step 1: Get viral news
        print("Step 1: Fetching viral news...")
        articles = get_trending_news()
        
        if not articles:
            print("No articles found")
            return False
        
        print(f"Found {len(articles)} articles")
        
        # Step 2: Select viral topic
        print("\nStep 2: Selecting viral topic...")
        viral_article = select_viral_topic(articles)
        
        if not viral_article:
            print("No viral topic selected")
            return False
        
        print(f"Selected: {viral_article['title']}")
        
        # Step 3: Generate caption
        print("\nStep 3: Generating caption...")
        caption = generate_facebook_caption(viral_article)
        
        if not caption:
            print("Caption generation failed")
            return False
        
        print(f"Caption generated ({len(caption)} characters)")
        
        # Step 4: Generate simple video
        print("\nStep 4: Generating simple video...")
        video_file = generate_simple_video(viral_article)
        
        if not video_file or not os.path.exists(video_file):
            print("Video generation failed")
            return False
        
        print(f"Video generated: {video_file}")
        print(f"Video size: {os.path.getsize(video_file)} bytes")
        
        # Step 5: Post to Facebook
        print("\nStep 5: Posting to Facebook...")
        success = post_to_facebook_page(caption, video_file)
        
        # Clean up
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"Cleaned up video file")
        except:
            pass
        
        if success:
            print("\nSUCCESS: Working video post published!")
            return True
        else:
            print("\nFAILED: Could not post to Facebook")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = create_working_video_post()
    
    if success:
        print("\n" + "="*60)
        print("WORKING VIDEO POST SUCCESSFUL!")
        print("Video generation is now working")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("VIDEO POST FAILED!")
        print("="*60)


