#!/usr/bin/env python3
"""
Create appealing subtitles with modern styling and effects
"""

import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from datetime import datetime

def create_appealing_subtitles(video_path, subtitle_text, output_path):
    """Create appealing subtitles with modern styling"""
    
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
            font_size = int(height * 0.08)  # 8% of video height
            max_width = int(width * 0.9)    # 90% of video width
            y_position = height * 0.75      # 75% from top
        else:
            font_size = int(height * 0.12)  # 12% of video height
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
        
        # Create subtitle clips with modern styling
        subtitle_clips = []
        line_height = font_size * 1.4
        
        for i, line in enumerate(lines):
            # Calculate position for each line
            if len(lines) == 1:
                y_pos = y_position
            else:
                total_height = len(lines) * line_height
                start_y = y_position - (total_height / 2) + (i * line_height)
                y_pos = start_y + line_height
            
            # Create main text with modern styling
            main_text = TextClip(
                text=line,
                font_size=font_size,
                color='white',
                stroke_color='black',
                stroke_width=int(font_size * 0.08),  # 8% of font size
                method='caption',
                size=(max_width, None)
            )
            
            # Create shadow effect (slightly offset)
            shadow_text = TextClip(
                text=line,
                font_size=font_size,
                color='black',
                stroke_color='black',
                stroke_width=int(font_size * 0.1),
                method='caption',
                size=(max_width, None)
            )
            
            # Position main text
            main_text = main_text.with_position(('center', y_pos))
            main_text = main_text.with_start(0.5 + (i * 0.15))  # Staggered appearance
            main_text = main_text.with_duration(duration - 1 - (i * 0.15))
            
            # Position shadow text (slightly offset for depth)
            shadow_text = shadow_text.with_position(('center', y_pos + 3))
            shadow_text = shadow_text.with_start(0.5 + (i * 0.15))
            shadow_text = shadow_text.with_duration(duration - 1 - (i * 0.15))
            
            subtitle_clips.extend([shadow_text, main_text])
        
        # Create semi-transparent background for better readability
        background = ColorClip(
            size=(width, int(font_size * 2.5)),
            color=(0, 0, 0),
            duration=duration - 1
        ).with_position(('center', y_position - font_size)).with_start(0.5)
        
        # Make background semi-transparent
        background = background.with_opacity(0.7)
        
        # Create composite video
        all_clips = [video, background] + subtitle_clips
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
        background.close()
        for clip in subtitle_clips:
            clip.close()
        
        print(f"SUCCESS: Appealing subtitles added to {output_path}")
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
    
    # Create appealing subtitle text
    subtitle_text = "BREAKING: MILLIONS EXPOSED IN 2024'S BIGGEST DATA BREACH"
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"appealing_subtitle_video_{timestamp}.mp4"
    
    print("="*60)
    print("CREATING APPEALING SUBTITLES")
    print("="*60)
    print(f"Input video: {video_file}")
    print(f"Subtitle: {subtitle_text}")
    print(f"Output: {output_file}")
    print("="*60)
    
    success = create_appealing_subtitles(video_file, subtitle_text, output_file)
    
    if success:
        print("\n" + "="*60)
        print("APPEALING SUBTITLES COMPLETE!")
        print("="*60)
        print(f"Original video: {video_file}")
        print(f"New video with appealing subtitles: {output_file}")
        print("="*60)
        print("\nFEATURES ADDED:")
        print("✅ Shadow effect for depth and readability")
        print("✅ Staggered text appearance for dynamic feel")
        print("✅ Semi-transparent background for contrast")
        print("✅ Bold stroke for maximum visibility")
        print("✅ Optimized sizing for Reels format")
        print("✅ Professional typography")
        print("="*60)
        print("\nREVIEW THE VIDEO:")
        print(f"1. Open: {output_file}")
        print("2. Check the visual appeal and readability")
        print("3. If approved, run: python approve_appealing_post.py")
        print("="*60)
    
    return success

if __name__ == "__main__":
    main()



