# test_system.py - Test the viral news automation system
from news_fetcher import get_trending_news, select_viral_topic
from content_generator import generate_facebook_caption, generate_post_image
from facebook_api import test_facebook_connection

def test_system():
    """Test all components of the system"""
    print("TESTING VIRAL NEWS AUTOMATION SYSTEM")
    print("="*50)
    
    # Test 1: Facebook Connection
    print("\n1. Testing Facebook API connection...")
    if test_facebook_connection():
        print("SUCCESS: Facebook API connection successful")
    else:
        print("FAILED: Facebook API connection failed")
        return False
    
    # Test 2: News Fetching
    print("\n2. Testing news fetching...")
    try:
        articles = get_trending_news()
        if articles:
            print(f"SUCCESS: Fetched {len(articles)} articles")
            print(f"   Sample: {articles[0]['title'][:50]}...")
        else:
            print("FAILED: No articles fetched")
            return False
    except Exception as e:
        print(f"FAILED: News fetching failed: {e}")
        return False
    
    # Test 3: Viral Topic Selection
    print("\n3. Testing viral topic selection...")
    try:
        viral_article = select_viral_topic(articles)
        if viral_article:
            print(f"SUCCESS: Selected viral topic: {viral_article['title'][:50]}...")
        else:
            print("FAILED: No viral topic selected")
            return False
    except Exception as e:
        print(f"FAILED: Viral topic selection failed: {e}")
        return False
    
    # Test 4: Caption Generation
    print("\n4. Testing caption generation...")
    try:
        caption = generate_facebook_caption(viral_article)
        if caption:
            print(f"SUCCESS: Caption generated ({len(caption)} characters)")
            print(f"   Preview: {caption[:100]}...")
        else:
            print("FAILED: No caption generated")
            return False
    except Exception as e:
        print(f"FAILED: Caption generation failed: {e}")
        return False
    
    # Test 5: Image Generation
    print("\n5. Testing image generation...")
    try:
        image_path = generate_post_image(viral_article)
        if image_path:
            print(f"SUCCESS: Image generated: {image_path}")
        else:
            print("FAILED: No image generated")
            return False
    except Exception as e:
        print(f"FAILED: Image generation failed: {e}")
        return False
    
    print("\nALL TESTS PASSED! System is ready to run.")
    return True

if __name__ == "__main__":
    test_system()
