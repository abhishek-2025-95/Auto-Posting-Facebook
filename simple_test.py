# simple_test.py - Simple test of the viral news system
from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_video

def simple_test():
    """Test the core functionality without Facebook posting"""
    print("SIMPLE TEST - VIRAL NEWS SYSTEM")
    print("="*40)
    
    # Test 1: News Fetching
    print("\n1. Testing news fetching...")
    try:
        articles = get_trending_news()
        if articles:
            print(f"SUCCESS: Fetched {len(articles)} articles")
            print(f"   Sample: {articles[0]['title'][:60]}...")
        else:
            print("FAILED: No articles fetched")
            return False
    except Exception as e:
        print(f"FAILED: News fetching failed: {e}")
        return False
    
    # Test 2: Viral Topic Selection
    print("\n2. Testing viral topic selection...")
    try:
        viral_article = select_viral_topic(articles)
        if viral_article:
            print(f"SUCCESS: Selected viral topic")
            print(f"   Title: {viral_article['title']}")
            print(f"   Description: {viral_article['description'][:80]}...")
        else:
            print("FAILED: No viral topic selected")
            return False
    except Exception as e:
        print(f"FAILED: Viral topic selection failed: {e}")
        return False
    
    # Test 3: Caption Generation
    print("\n3. Testing caption generation...")
    try:
        caption = generate_facebook_caption(viral_article)
        if caption:
            print(f"SUCCESS: Caption generated ({len(caption)} characters)")
            print(f"   Preview: {caption[:150]}...")
        else:
            print("FAILED: No caption generated")
            return False
    except Exception as e:
        print(f"FAILED: Caption generation failed: {e}")
        return False
    
    # Test 4: Video Generation
    print("\n4. Testing video generation...")
    try:
        video_path = generate_post_video(viral_article)
        if video_path:
            print(f"SUCCESS: Video generated: {video_path}")
        else:
            print("FAILED: No video generated")
            return False
    except Exception as e:
        print(f"FAILED: Video generation failed: {e}")
        return False
    
    print("\nALL CORE TESTS PASSED!")
    print("System is ready - just need to update Facebook token")
    return True

if __name__ == "__main__":
    simple_test()

