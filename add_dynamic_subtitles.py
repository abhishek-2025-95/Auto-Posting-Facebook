#!/usr/bin/env python3
"""
Add dynamic, hook-appealing subtitles to video with breaking news vibe
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from datetime import datetime

def create_dynamic_subtitles(video_path, subtitle_text, output_path):
    """Add dynamic subtitles to video with breaking news vibe"""
    
    print(f"Processing video: {video_path}")
    print(f"Subtitle: {subtitle_text}")
    
    try:
        # Load video
        video = VideoFileClip(video_path)
        duration = video.duration
        
        print(f"Video duration: {duration:.2f} seconds")
        
        # Create dynamic subtitle with breaking news style
        subtitle = TextClip(
            text=subtitle_text,
            font_size=60,
            color='white',
            stroke_color='red',
            stroke_width=3
        ).set_position(('center', 'bottom')).set_start(0.5).set_duration(duration - 1)
        
        # Add a pulsing effect by scaling the text
        def make_pulse(t):
            return 1 + 0.1 * (1 + (t * 2) % 1)  # Subtle pulsing effect
        
        subtitle = subtitle.resize(make_pulse)
        
        # Create composite video
        final_video = CompositeVideoClip([video, subtitle])
        
        # Write the result
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up
        video.close()
        final_video.close()
        
        print(f"SUCCESS: Dynamic subtitles added to {output_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def add_subtitles_to_video():
    """Add dynamic subtitles to the specified video"""
    
    video_file = "preview_video_20251022_135420.mp4"
    
    if not os.path.exists(video_file):
        print(f"Video file not found: {video_file}")
        return False
    
    # Create hook-appealing subtitle with breaking news vibe
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("ADDING DYNAMIC SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = create_dynamic_subtitles(video_file, subtitle_text, output_file)
    
    if success:
        print("\n" + "="*60)
        print("SUBTITLE ADDITION COMPLETE!")
        print("="*60)
        print(f"Original video: {video_file}")
        print(f"New video with subtitles: {output_file}")
        print("="*60)
        
        # Post the new video to Facebook
        print("\nPosting to Facebook...")
        from facebook_api import post_to_facebook_page
        from content_generator import generate_facebook_caption
        
        # Generate caption for the video
        article = {
            'title': 'BREAKING: Major Data Breach Exposes Millions of Americans',
            'description': 'Millions of American user records have been exposed in what experts are calling the largest data breach of 2024.',
            'source': 'Breaking News Alert'
        }
        
        caption = generate_facebook_caption(article)
        if caption:
            success = post_to_facebook_page(caption, output_file)
            if success:
                print("SUCCESS: Video with subtitles posted to Facebook!")
            else:
                print("FAILED: Could not post to Facebook")
        else:
            print("FAILED: Could not generate caption")
    
    return success

if __name__ == "__main__":
    add_subtitles_to_video()
