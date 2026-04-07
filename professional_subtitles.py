#!/usr/bin/env python3
"""
Create professional-grade subtitles for Reels with dynamic effects
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from datetime import datetime

def create_professional_subtitles(video_path, subtitle_text, output_path):
    """Create professional-grade subtitles optimized for Reels"""
    
    print(f"Processing video: {video_path}")
    print(f"Subtitle: {subtitle_text}")
    
    try:
        # Load video
        video = VideoFileClip(video_path)
        duration = video.duration
        width, height = video.size
        
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video resolution: {width}x{height}")
        
        # Check if video is vertical (Reels format)
        is_vertical = height > width
        print(f"Video orientation: {'Vertical (Reels)' if is_vertical else 'Horizontal'}")
        
        # Calculate optimal font size based on video dimensions
        if is_vertical:
            # For vertical videos (Reels), use larger font
            font_size = int(height * 0.08)  # 8% of video height
            max_width = int(width * 0.85)   # 85% of video width
        else:
            # For horizontal videos
            font_size = int(height * 0.12)  # 12% of video height
            max_width = int(width * 0.8)    # 80% of video width
        
        print(f"Calculated font size: {font_size}")
        print(f"Max text width: {max_width}")
        
        # Split text into multiple lines if too long
        words = subtitle_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Rough estimation of text width (font_size * 0.6 is approximate)
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
        
        # Create subtitle clips for each line
        subtitle_clips = []
        line_height = font_size * 1.2  # Line spacing
        
        for i, line in enumerate(lines):
            # Calculate vertical position for each line
            if len(lines) == 1:
                y_pos = height * 0.85  # Single line at 85% from top
            else:
                # Multiple lines centered
                total_height = len(lines) * line_height
                start_y = (height - total_height) / 2 + (i * line_height)
                y_pos = start_y + line_height
            
            # Create text clip with professional styling
            text_clip = TextClip(
                text=line,
                font_size=font_size,
                color='white',
                stroke_color='black',
                stroke_width=int(font_size * 0.08),  # 8% of font size
                method='caption',
                size=(max_width, None)
            )
            
            # Position the text
            text_clip = text_clip.with_position(('center', y_pos))
            text_clip = text_clip.with_start(0.5)
            text_clip = text_clip.with_duration(duration - 1)
            
            # Add subtle animation effect (removed for now due to MoviePy version)
            # text_clip = text_clip.resize(make_glow)
            subtitle_clips.append(text_clip)
        
        # Create composite video with all subtitle clips
        all_clips = [video] + subtitle_clips
        final_video = CompositeVideoClip(all_clips)
        
        # Write the result with high quality
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=30,  # High frame rate for smooth playback
            preset='medium',  # Good balance of quality and speed
            ffmpeg_params=['-crf', '18']  # High quality encoding
        )
        
        # Clean up
        video.close()
        final_video.close()
        for clip in subtitle_clips:
            clip.close()
        
        print(f"SUCCESS: Professional subtitles added to {output_path}")
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
    
    # Create professional subtitle text
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"professional_subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("CREATING PROFESSIONAL SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = create_professional_subtitles(video_file, subtitle_text, output_file)
    
    if success:
        print("\n" + "="*60)
        print("PROFESSIONAL SUBTITLES COMPLETE!")
        print("="*60)
        print(f"Original video: {video_file}")
        print(f"New video with professional subtitles: {output_file}")
        print("="*60)
        print("\nREVIEW THE VIDEO:")
        print(f"1. Open: {output_file}")
        print("2. Check subtitle positioning and readability")
        print("3. Verify it's Reels-friendly")
        print("4. If approved, run: python approve_and_post.py")
        print("="*60)
    
    return success

if __name__ == "__main__":
    main()
