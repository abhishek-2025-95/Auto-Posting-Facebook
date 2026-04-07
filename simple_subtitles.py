#!/usr/bin/env python3
"""
Add simple subtitles to video using a different approach
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from datetime import datetime

def add_simple_subtitles(video_path, subtitle_text, output_path):
    """Add simple subtitles to video"""
    
    print(f"Processing video: {video_path}")
    print(f"Subtitle: {subtitle_text}")
    
    try:
        # Load video
        video = VideoFileClip(video_path)
        duration = video.duration
        
        print(f"Video duration: {duration:.2f} seconds")
        
        # Create simple subtitle
        subtitle = TextClip(
            text=subtitle_text,
            font_size=50,
            color='white',
            stroke_color='red',
            stroke_width=2
        )
        
        # Position at bottom center
        subtitle = subtitle.with_position(('center', 'bottom'))
        subtitle = subtitle.with_start(0.5)
        subtitle = subtitle.with_duration(duration - 1)
        
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
        
        print(f"SUCCESS: Subtitles added to {output_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    video_file = "preview_video_20251022_135420.mp4"
    
    if not os.path.exists(video_file):
        print(f"Video file not found: {video_file}")
        return False
    
    # Create hook-appealing subtitle
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("ADDING SIMPLE SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = add_simple_subtitles(video_file, subtitle_text, output_file)
    
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
    main()
