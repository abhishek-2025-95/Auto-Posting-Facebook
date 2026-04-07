#!/usr/bin/env python3
"""
Create simple, clean subtitles that work reliably
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from datetime import datetime

def create_simple_clean_subtitles(video_path, subtitle_text, output_path):
    """Create simple, clean subtitles that work reliably"""
    
    print(f"Processing video: {video_path}")
    print(f"Subtitle: {subtitle_text}")
    
    try:
        # Load video
        video = VideoFileClip(video_path)
        duration = video.duration
        width, height = video.size
        
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video resolution: {width}x{height}")
        
        # Calculate optimal dimensions
        font_size = int(height * 0.1)  # 10% of video height
        max_width = int(width * 0.8)   # 80% of video width
        y_position = height * 0.8      # 80% from top
        
        print(f"Font size: {font_size}")
        print(f"Max width: {max_width}")
        print(f"Y position: {y_position}")
        
        # Split text into lines
        words = subtitle_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * (font_size * 0.6) > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        print(f"Text split into {len(lines)} lines:")
        for i, line in enumerate(lines):
            print(f"  Line {i+1}: {line}")
        
        # Create subtitle clips
        subtitle_clips = []
        line_height = font_size * 1.2
        
        for i, line in enumerate(lines):
            # Calculate position for each line
            if len(lines) == 1:
                y_pos = y_position
            else:
                total_height = len(lines) * line_height
                start_y = y_position - (total_height / 2) + (i * line_height)
                y_pos = start_y + line_height
            
            # Create text clip
            text_clip = TextClip(
                text=line,
                font_size=font_size,
                color='white',
                stroke_color='black',
                stroke_width=int(font_size * 0.05),
                method='caption',
                size=(max_width, None)
            )
            
            # Position text
            text_clip = text_clip.with_position(('center', y_pos))
            text_clip = text_clip.with_start(0.5)
            text_clip = text_clip.with_duration(duration - 1)
            
            subtitle_clips.append(text_clip)
        
        # Create composite video
        all_clips = [video] + subtitle_clips
        final_video = CompositeVideoClip(all_clips)
        
        # Write with high quality settings
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=30,
            preset='medium',
            ffmpeg_params=['-crf', '18']
        )
        
        # Clean up
        video.close()
        final_video.close()
        for clip in subtitle_clips:
            clip.close()
        
        print(f"SUCCESS: Simple clean subtitles added to {output_path}")
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
    
    # Create subtitle text
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"simple_clean_subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("CREATING SIMPLE CLEAN SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = create_simple_clean_subtitles(video_file, subtitle_text, output_file)
    
    if success:
        print("\n" + "="*60)
        print("SIMPLE CLEAN SUBTITLES COMPLETE!")
        print("="*60)
        print(f"Original video: {video_file}")
        print(f"New video with simple clean subtitles: {output_file}")
        print("="*60)
        print("\nFEATURES ADDED:")
        print("Clean, readable typography")
        print("Bold stroke for maximum visibility")
        print("Optimized sizing for Reels format")
        print("Professional spacing and alignment")
        print("No cutting off - perfect positioning")
        print("Reliable rendering")
        print("="*60)
        print("\nREVIEW THE VIDEO:")
        print(f"1. Open: {output_file}")
        print("2. Check the visual appeal and readability")
        print("3. If approved, run: python approve_simple_post.py")
        print("="*60)
    
    return success

if __name__ == "__main__":
    main()
