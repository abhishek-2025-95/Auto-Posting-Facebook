#!/usr/bin/env python3
"""
Debug why video generation is failing
"""

import os
from content_generator import generate_video_prompt_with_gemini, generate_video_with_veo3
from news_fetcher import get_trending_news, select_viral_topic

def debug_video_generation():
    """Debug video generation issues"""
    print("="*60)
    print("DEBUGGING VIDEO GENERATION FAILURE")
    print("="*60)
    
    # Step 1: Check Veo 3 quota status
    print("Step 1: Checking Veo 3 quota status...")
    try:
        from check_veo3_status import check_veo3_quota
        quota_info = check_veo3_quota()
        print(f"Veo 3 quota status: {quota_info}")
    except Exception as e:
        print(f"Could not check Veo 3 quota: {e}")
    
    # Step 2: Test video prompt generation
    print("\nStep 2: Testing video prompt generation...")
    try:
        articles = get_trending_news()
        if articles:
            viral_article = select_viral_topic(articles)
            if viral_article:
                print(f"Selected article: {viral_article['title'][:50]}...")
                
                # Test prompt generation
                video_prompt = generate_video_prompt_with_gemini(viral_article)
                if video_prompt:
                    print(f"Video prompt generated successfully ({len(video_prompt)} chars)")
                    print(f"Prompt preview: {video_prompt[:200]}...")
                else:
                    print("Video prompt generation failed")
                    return False
            else:
                print("No viral article selected")
                return False
        else:
            print("No articles found")
            return False
    except Exception as e:
        print(f"Error in prompt generation: {e}")
        return False
    
    # Step 3: Test Veo 3 API directly
    print("\nStep 3: Testing Veo 3 API directly...")
    try:
        # Test with a simple prompt
        test_prompt = "A simple 8-second video of a teenager with a bag of chips at a security scanner"
        
        print(f"Testing with simple prompt: {test_prompt}")
        video_file = generate_video_with_veo3(test_prompt, duration_seconds=8, aspect_ratio="16:9", resolution="1080p")
        
        if video_file and os.path.exists(video_file):
            print(f"SUCCESS: Video generated - {video_file}")
            print(f"Video size: {os.path.getsize(video_file)} bytes")
            return True
        else:
            print("FAILED: No video generated")
            return False
            
    except Exception as e:
        print(f"Error in Veo 3 generation: {e}")
        return False

def check_api_keys():
    """Check if API keys are properly configured"""
    print("\n" + "="*60)
    print("CHECKING API CONFIGURATION")
    print("="*60)
    
    try:
        from config import GEMINI_API_KEY
        
        if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            print("SUCCESS: Gemini API key is configured")
        else:
            print("ERROR: Gemini API key not configured")
            return False
        
        # Check if Google GenAI is properly imported
        try:
            from google import genai
            print("SUCCESS: Google GenAI library imported")
        except ImportError as e:
            print(f"ERROR: Google GenAI library not available: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error checking configuration: {e}")
        return False

def test_simple_video_generation():
    """Test with the simplest possible video generation"""
    print("\n" + "="*60)
    print("TESTING SIMPLE VIDEO GENERATION")
    print("="*60)
    
    try:
        from google import genai
        from config import GEMINI_API_KEY
        
        # Initialize client
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test with minimal prompt
        print("Testing with minimal Veo 3 prompt...")
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt="A simple 8-second video of a person walking",
            config=genai.types.GenerateVideosConfig(
                negative_prompt="blurry, low quality",
            ),
        )
        
        print("Video generation started...")
        print("This may take a few minutes...")
        
        # Wait for completion
        import time
        max_wait = 300  # 5 minutes max
        wait_time = 0
        
        while not operation.done and wait_time < max_wait:
            print(f"Waiting... ({wait_time}s)")
            time.sleep(10)
            wait_time += 10
            operation = client.operations.get(operation)
        
        if operation.done:
            if operation.result and operation.result.generated_videos:
                print("SUCCESS: Video generation completed")
                return True
            else:
                print("FAILED: No video generated")
                return False
        else:
            print("TIMEOUT: Video generation took too long")
            return False
            
    except Exception as e:
        print(f"Error in simple video generation: {e}")
        return False

if __name__ == "__main__":
    print("DIAGNOSING VIDEO GENERATION FAILURE")
    print("="*60)
    
    # Check API configuration
    config_ok = check_api_keys()
    
    if config_ok:
        # Test simple video generation
        simple_ok = test_simple_video_generation()
        
        if simple_ok:
            print("\nSUCCESS: Video generation is working")
            print("The issue may be with complex prompts or quota limits")
        else:
            print("\nFAILED: Video generation is not working")
            print("Check Veo 3 quota and API configuration")
    else:
        print("\nFAILED: API configuration issues")
        print("Fix API keys and dependencies first")


