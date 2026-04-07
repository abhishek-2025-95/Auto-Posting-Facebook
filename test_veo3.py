#!/usr/bin/env python3
"""
Test Veo 3 video generation
"""

import time
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

def test_veo3_video():
    """Test Veo 3 video generation"""
    print("Testing Veo 3 video generation...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test with a simple prompt
        test_prompt = "A professional business meeting room with people discussing important matters, cinematic lighting"
        
        print("Starting video generation...")
        
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                negative_prompt="crowded, noisy",
            ),
        )
        
        print("Video generation started, waiting for completion...")
        
        # Wait for the video to be generated
        while not operation.done:
            print("Generating video... (this may take 2-3 minutes)")
            time.sleep(20)
            operation = client.operations.get(operation)
        
        # Get the generated video
        if operation.result and operation.result.generated_videos:
            generated_video = operation.result.generated_videos[0]
            
            # Download and save the video
            video_path = "test_veo3_video.mp4"
            client.files.download(file=generated_video.video)
            generated_video.video.save(video_path)
            
            print(f"SUCCESS: Veo 3 video saved as {video_path}")
            return True
        else:
            print("No video generated")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_veo3_video()
