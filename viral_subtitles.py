#!/usr/bin/env python3
"""
Create viral, appealing subtitles with modern effects and animations
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from datetime import datetime

def create_viral_subtitles(video_path, subtitle_text, output_path):
    """Create viral, appealing subtitles with modern effects"""
    
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
        
        # Calculate optimal dimensions
        if is_vertical:
            font_size = int(height * 0.1)  # 10% of video height
            max_width = int(width * 0.9)   # 90% of video width
            y_position = height * 0.75     # 75% from top
        else:
            font_size = int(height * 0.15)  # 15% of video height
            max_width = int(width * 0.85)   # 85% of video width
            y_position = height * 0.8       # 80% from top
        
        print(f"Font size: {font_size}")
        print(f"Max width: {max_width}")
        print(f"Y position: {y_position}")
        
        # Split text into lines for better visual impact
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
        
        # Create animated subtitle clips
        subtitle_clips = []
        line_height = font_size * 1.3
        
        for i, line in enumerate(lines):
            # Calculate position for each line
            if len(lines) == 1:
                y_pos = y_position
            else:
                total_height = len(lines) * line_height
                start_y = y_position - (total_height / 2) + (i * line_height)
                y_pos = start_y + line_height
            
            # Create main text with bold styling
            main_text = TextClip(
                text=line,
                font_size=font_size,
                color='white',
                stroke_color='black',
                stroke_width=int(font_size * 0.1),  # 10% of font size for bold stroke
                method='caption',
                size=(max_width, None)
            )
            
            # Create glow effect (slightly larger, semi-transparent)
            glow_text = TextClip(
                text=line,
                font_size=int(font_size * 1.1),
                color='yellow',
                stroke_color='orange',
                stroke_width=int(font_size * 0.05),
                method='caption',
                size=(max_width, None)
            )
            
            # Position main text
            main_text = main_text.with_position(('center', y_pos))
            main_text = main_text.with_start(0.5 + (i * 0.2))  # Staggered appearance
            main_text = main_text.with_duration(duration - 1 - (i * 0.2))
            
            # Position glow text (behind main text)
            glow_text = glow_text.with_position(('center', y_pos))
            glow_text = glow_text.with_start(0.5 + (i * 0.2))
            glow_text = glow_text.with_duration(duration - 1 - (i * 0.2))
            
            # Add pulsing animation
            def pulse_effect(t):
                return 1 + 0.1 * (1 + (t * 2) % 1)
            
            # Apply effects
            main_text = main_text.resize(pulse_effect)
            glow_text = glow_text.resize(pulse_effect)
            
            subtitle_clips.extend([glow_text, main_text])
        
        # Create background highlight for better readability
        highlight = ColorClip(
            size=(width, int(font_size * 2)),
            color=(0, 0, 0),
            duration=duration - 1
        ).with_position(('center', y_position - font_size)).with_start(0.5)
        
        # Create composite video
        all_clips = [video, highlight] + subtitle_clips
        final_video = CompositeVideoClip(all_clips)
        
        # Write with high quality settings
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=30,
            preset='slow',  # Better quality
            ffmpeg_params=['-crf', '15']  # Very high quality
        )
        
        # Clean up
        video.close()
        final_video.close()
        highlight.close()
        for clip in subtitle_clips:
            clip.close()
        
        print(f"SUCCESS: Viral subtitles added to {output_path}")
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
    
    # Create viral subtitle text
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"viral_subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("CREATING VIRAL SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = create_viral_subtitles(video_file, subtitle_text, output_file)
    
    if success:
        print("\n" + "="*60)
        print("VIRAL SUBTITLES COMPLETE!")
        print("="*60)
        print(f"Original video: {video_file}")
        print(f"New video with viral subtitles: {output_file}")
        print("="*60)
        print("\nFEATURES ADDED:")
        print("✅ Glow effect with yellow/orange colors")
        print("✅ Pulsing animation for attention")
        print("✅ Staggered text appearance")
        print("✅ Background highlight for readability")
        print("✅ Bold stroke for maximum contrast")
        print("✅ Optimized for Reels format")
        print("="*60)
        print("\nREVIEW THE VIDEO:")
        print(f"1. Open: {output_file}")
        print("2. Check the viral appeal and readability")
        print("3. If approved, run: python approve_viral_post.py")
        print("="*60)
    
    return success

if __name__ == "__main__":
    main()



