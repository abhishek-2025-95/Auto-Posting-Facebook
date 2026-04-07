#!/usr/bin/env python3
"""
Video Subtitle Enhancer - Add viral subtitles to videos
"""

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
import os
import re
from datetime import datetime

def extract_key_phrases(text, max_phrases=5):
    """Extract key phrases from text for subtitles"""
    # Remove hashtags and clean text
    clean_text = re.sub(r'#\w+', '', text)
    clean_text = re.sub(r'http\S+', '', clean_text)
    clean_text = clean_text.strip()
    
    # Split into sentences and extract key phrases
    sentences = [s.strip() for s in clean_text.split('.') if s.strip()]
    
    # Take first few sentences as key phrases
    key_phrases = sentences[:max_phrases]
    
    # Add some viral-style phrases
    viral_phrases = [
        "BREAKING NEWS",
        "MAJOR ALERT",
        "YOU NEED TO KNOW",
        "SHARE THIS NOW",
        "VIRAL UPDATE"
    ]
    
    # Combine viral phrases with content
    subtitle_phrases = []
    if key_phrases:
        subtitle_phrases.append(viral_phrases[0])
        subtitle_phrases.extend(key_phrases[:3])
        if len(key_phrases) > 3:
            subtitle_phrases.append(viral_phrases[1])
    
    return subtitle_phrases

def create_viral_subtitles(video_path, caption_text, output_path):
    """Add viral subtitles to video"""
    print("Adding viral subtitles to video...")
    
    try:
        # Load the video
        video = VideoFileClip(video_path)
        duration = video.duration
        
        # Extract key phrases
        phrases = extract_key_phrases(caption_text)
        
        # Create subtitle clips
        subtitle_clips = []
        
        # Calculate timing for each subtitle
        phrase_duration = duration / len(phrases) if phrases else 2
        
        for i, phrase in enumerate(phrases):
            start_time = i * phrase_duration
            end_time = min((i + 1) * phrase_duration, duration)
            
            # Create text clip with viral styling
            txt_clip = TextClip(
                phrase,
                fontsize=60,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(video.w - 100, None)
            ).set_position(('center', 'bottom')).set_start(start_time).set_end(end_time)
            
            subtitle_clips.append(txt_clip)
        
        # Add a pulsing effect to the first subtitle
        if subtitle_clips:
            first_clip = subtitle_clips[0]
            # Make it pulse
            first_clip = first_clip.resize(lambda t: 1 + 0.1 * abs(t % 1 - 0.5))
            subtitle_clips[0] = first_clip
        
        # Composite the video with subtitles
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
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
        
        print(f"SUCCESS: Viral subtitles added to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error adding subtitles: {e}")
        return None

def create_enhanced_video_with_subtitles(article):
    """Create enhanced video with viral subtitles"""
    print("Creating enhanced video with subtitles...")
    
    try:
        from content_generator import generate_video_with_veo3, generate_facebook_caption
        
        # Generate caption
        caption = generate_facebook_caption(article)
        
        # Generate base video
        base_video = generate_video_with_veo3(f"Professional news documentary style 8-second video representing: {article['title']}. High quality, cinematic, 1080p, 16:9 aspect ratio, with appropriate audio.")
        
        if not base_video:
            print("Failed to generate base video")
            return None
        
        # Add viral subtitles
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        enhanced_video = f"enhanced_video_{timestamp}.mp4"
        
        result = create_viral_subtitles(base_video, caption, enhanced_video)
        
        if result:
            # Clean up base video
            try:
                os.remove(base_video)
            except:
                pass
            
            return result
        else:
            return base_video
            
    except Exception as e:
        print(f"Error creating enhanced video: {e}")
        return None

if __name__ == "__main__":
    # Test with sample content
    test_article = {
        'title': 'Major Tech Company Faces Data Breach Scandal',
        'description': 'Millions of user records exposed in what experts call the largest breach of 2024'
    }
    
    result = create_enhanced_video_with_subtitles(test_article)
    if result:
        print(f"Enhanced video created: {result}")
    else:
        print("Failed to create enhanced video")



