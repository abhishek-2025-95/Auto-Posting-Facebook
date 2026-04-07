#!/usr/bin/env python3
"""
Test the improved video prompt generation
"""

from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_video_prompt_with_gemini

def test_improved_video_prompt():
    """Test the improved video prompt generation"""
    print("="*60)
    print("TESTING IMPROVED VIDEO PROMPT GENERATION")
    print("="*60)
    
    # Get viral news
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
    
    # Generate improved video prompt
    print(f"\nGenerating improved video prompt...")
    video_prompt = generate_video_prompt_with_gemini(viral_article)
    
    print(f"\nGenerated video prompt:")
    print("="*40)
    print(video_prompt)
    print("="*40)
    
    # Check relevance
    print(f"\nRelevance check:")
    news_title = viral_article['title'].lower()
    prompt_lower = video_prompt.lower()
    
    # Look for specific keywords from the news
    if 'doritos' in news_title and 'doritos' in prompt_lower:
        print("SUCCESS: Video prompt mentions Doritos")
    elif 'doritos' in news_title:
        print("ISSUE: News is about Doritos but video prompt doesn't mention it")
    
    if 'ai' in news_title and 'ai' in prompt_lower:
        print("SUCCESS: Video prompt mentions AI")
    elif 'ai' in news_title:
        print("ISSUE: News is about AI but video prompt doesn't mention it")
    
    if 'teen' in news_title and ('teen' in prompt_lower or 'student' in prompt_lower):
        print("SUCCESS: Video prompt mentions teen/student")
    elif 'teen' in news_title:
        print("ISSUE: News is about teen but video prompt doesn't mention it")
    
    if 'cop' in news_title and ('police' in prompt_lower or 'cop' in prompt_lower):
        print("SUCCESS: Video prompt mentions police/cops")
    elif 'cop' in news_title:
        print("ISSUE: News is about cops but video prompt doesn't mention it")
    
    # Check if prompt is specific vs generic
    generic_terms = ['professional', 'cinematic', 'dramatic', 'news', 'breaking', 'urgent', 'cityscape', 'skyline']
    specific_terms = ['doritos', 'bag', 'gun', 'teen', 'student', 'ai', 'metal detector', 'police', 'cop']
    
    generic_count = sum(1 for term in generic_terms if term in prompt_lower)
    specific_count = sum(1 for term in specific_terms if term in prompt_lower)
    
    print(f"\nPrompt analysis:")
    print(f"Generic terms: {generic_count}")
    print(f"Specific terms: {specific_count}")
    
    if specific_count > generic_count:
        print("SUCCESS: Video prompt is specific to the news story")
    else:
        print("ISSUE: Video prompt is too generic")
    
    return video_prompt

if __name__ == "__main__":
    test_improved_video_prompt()


