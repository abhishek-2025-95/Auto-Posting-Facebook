#!/usr/bin/env python3
"""
Test the enhanced viral news system
"""

from news_fetcher import get_trending_news, select_viral_topic

def test_enhanced_news():
    print("="*60)
    print("TESTING ENHANCED VIRAL NEWS SYSTEM")
    print("="*60)
    
    # Get articles
    articles = get_trending_news()
    print(f"\nFound {len(articles)} articles")
    
    if articles:
        print("\nArticles found:")
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. TITLE: {article['title']}")
            print(f"   SOURCE: {article['source']}")
            print(f"   PRIORITY: {article.get('priority', 'N/A')}")
            print(f"   URL: {article.get('url', 'No URL')}")
        
        # Test viral selection
        print(f"\n" + "="*40)
        print("VIRAL SELECTION:")
        print("="*40)
        
        viral_article = select_viral_topic(articles)
        print(f"\nSelected: {viral_article['title']}")
        print(f"Source: {viral_article['source']}")
        print(f"Reason: {viral_article.get('viral_reason', 'No reason')}")
        
        # Check improvements
        print(f"\n" + "="*40)
        print("IMPROVEMENTS CHECK:")
        print("="*40)
        
        # Check for viral keywords in titles
        viral_keywords = ['breaking', 'urgent', 'exclusive', 'shocking', 'crisis', 'scandal']
        found_keywords = []
        for keyword in viral_keywords:
            if keyword.lower() in viral_article['title'].lower():
                found_keywords.append(keyword)
        
        print(f"Viral keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
        
        # Check source quality
        high_quality_sources = ['CNN', 'BBC', 'Reuters', 'AP', 'NPR', 'Fox News', 'MSNBC', 'ABC', 'CBS', 'NBC']
        source_quality = "High" if viral_article['source'] in high_quality_sources else "Medium"
        print(f"Source quality: {source_quality}")
        
        # Overall assessment
        if found_keywords and source_quality == "High":
            print(f"\nSUCCESS: Enhanced system working - viral content from quality source!")
        elif found_keywords:
            print(f"\nGOOD: Viral keywords found, but source could be better")
        elif source_quality == "High":
            print(f"\nGOOD: Quality source, but could use more viral keywords")
        else:
            print(f"\nNEEDS IMPROVEMENT: Limited viral potential")
    else:
        print("\nNo articles found - using fallback content")

if __name__ == "__main__":
    test_enhanced_news()


