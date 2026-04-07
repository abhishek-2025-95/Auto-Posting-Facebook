#!/usr/bin/env python3
"""
Debug why video content doesn't match the news
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_video_prompt_with_gemini, generate_video_with_veo3
import json

def debug_video_content():
    """Debug the video generation process"""
    print("="*60)
    print("DEBUGGING VIDEO CONTENT RELEVANCE")
    print("="*60)
    
    # Get the same news article
    articles = get_trending_news()
    if not articles:
        print("No articles found")
        return
    
    viral_article = select_viral_topic(articles)
    if not viral_article:
        print("No viral article selected")
        return
    
    print(f"Selected news: {viral_article['title']}")
    print(f"Description: {viral_article['description'][:100]}...")
    
    # Step 1: Check the video prompt generation
    print(f"\n" + "="*40)
    print("STEP 1: VIDEO PROMPT GENERATION")
    print("="*40)
    
    video_prompt = generate_video_prompt_with_gemini(viral_article)
    print(f"Generated video prompt:")
    print(f"Length: {len(video_prompt)} characters")
    print(f"Content: {video_prompt}")
    
    # Step 2: Check what Gemini is actually asking for
    print(f"\n" + "="*40)
    print("STEP 2: ANALYZING PROMPT RELEVANCE")
    print("="*40)
    
    # Check if the prompt mentions the actual news
    news_keywords = ['doritos', 'bag', 'gun', 'teen', 'cops', 'ai', 'metal detector', 'swarmed']
    prompt_lower = video_prompt.lower()
    
    found_keywords = []
    for keyword in news_keywords:
        if keyword in prompt_lower:
            found_keywords.append(keyword)
    
    print(f"News keywords found in prompt: {found_keywords}")
    print(f"Relevance score: {len(found_keywords)}/{len(news_keywords)}")
    
    if len(found_keywords) >= 3:
        print("GOOD: Prompt seems relevant to the news")
    else:
        print("PROBLEM: Prompt may not be relevant to the news")
    
    # Step 3: Check the actual prompt structure
    print(f"\n" + "="*40)
    print("STEP 3: PROMPT STRUCTURE ANALYSIS")
    print("="*40)
    
    # Look for specific elements
    if 'doritos' in prompt_lower:
        print("✅ Mentions Doritos")
    else:
        print("❌ Missing Doritos reference")
    
    if 'gun' in prompt_lower or 'weapon' in prompt_lower:
        print("✅ Mentions gun/weapon")
    else:
        print("❌ Missing gun reference")
    
    if 'teen' in prompt_lower or 'student' in prompt_lower:
        print("✅ Mentions teen/student")
    else:
        print("❌ Missing teen reference")
    
    if 'police' in prompt_lower or 'cop' in prompt_lower:
        print("✅ Mentions police/cops")
    else:
        print("❌ Missing police reference")
    
    if 'ai' in prompt_lower or 'artificial intelligence' in prompt_lower:
        print("✅ Mentions AI")
    else:
        print("❌ Missing AI reference")
    
    # Step 4: Check if the prompt is too generic
    print(f"\n" + "="*40)
    print("STEP 4: GENERIC PROMPT CHECK")
    print("="*40)
    
    generic_terms = ['professional', 'cinematic', 'dramatic', 'news', 'breaking', 'urgent']
    generic_count = sum(1 for term in generic_terms if term in prompt_lower)
    
    print(f"Generic terms found: {generic_count}")
    if generic_count > 3:
        print("WARNING: Prompt may be too generic")
    else:
        print("GOOD: Prompt has specific content")
    
    # Step 5: Suggest improvements
    print(f"\n" + "="*40)
    print("STEP 5: SUGGESTED IMPROVEMENTS")
    print("="*40)
    
    if len(found_keywords) < 3:
        print("ISSUE: Video prompt doesn't reference the specific news story")
        print("SOLUTION: Improve the Gemini prompt to be more specific")
        print("RECOMMENDATION: Add more context about the actual incident")
    else:
        print("GOOD: Video prompt seems relevant")
    
    return video_prompt

def test_improved_video_prompt():
    """Test with an improved video prompt"""
    print(f"\n" + "="*60)
    print("TESTING IMPROVED VIDEO PROMPT")
    print("="*60)
    
    # Create a more specific prompt
    improved_prompt = """
    Create a highly detailed, cinematic video prompt for Google's Veo 3 to generate an 8-second 1080p, 16:9 video about this specific news story:
    
    NEWS STORY: "Teen Swarmed by Cops After AI Metal Detector Flags His Doritos Bag as a Gun"
    
    The video must show:
    - A teenager with a bag of Doritos
    - An AI metal detector system
    - Police officers responding
    - The confusion and absurdity of the situation
    - The visual contrast between a snack bag and a weapon
    
    Style: Documentary news style, dramatic lighting, showing the absurdity of the AI mistake
    """
    
    print("Improved prompt:")
    print(improved_prompt)
    
    return improved_prompt

if __name__ == "__main__":
    # Debug current video generation
    current_prompt = debug_video_content()
    
    # Test improved approach
    improved_prompt = test_improved_video_prompt()
    
    print(f"\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    
    if current_prompt and len(current_prompt) > 200:
        print("ISSUE IDENTIFIED: Video prompt may be too generic")
        print("SOLUTION: Need to make the prompt more specific to the actual news story")
        print("RECOMMENDATION: Update the Gemini prompt to include specific details")
    else:
        print("ISSUE: Video prompt generation may be failing")
        print("SOLUTION: Check Gemini API and prompt structure")


