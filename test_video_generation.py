#!/usr/bin/env python3
"""
Test Video Generation
Debug why video generation is failing
"""

def test_video_generation():
    """Test video generation with a simple example"""
    print("TESTING VIDEO GENERATION")
    print("="*50)
    
    try:
        from content_generator import generate_post_video
        
        # Create a simple test article
        test_article = {
            'title': 'Breaking: Major Tech News',
            'description': 'Important technology development that affects everyone',
            'url': 'https://example.com/news'
        }
        
        print(f"Test article: {test_article['title']}")
        print("\nGenerating video...")
        
        video_file = generate_post_video(test_article)
        
        if video_file and os.path.exists(video_file):
            print(f"SUCCESS: Video generated - {video_file}")
            return True
        else:
            print("FAILED: No video file generated")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    test_video_generation()


