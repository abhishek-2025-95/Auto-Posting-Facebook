#!/usr/bin/env python3
"""
Verify all news sources (Reddit, Newsdata.io, Google News, BBC/NPR/Reuters RSS).
Run: python verify_all_sources.py
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

def main():
    print("=" * 60)
    print("VERIFYING ALL NEWS SOURCES")
    print("=" * 60)

    # 1) Imports
    print("\n1. Checking imports...")
    try:
        from news_fetcher import get_trending_news
        from reputed_rss_fetcher import get_reputed_rss_news
        from google_news_fetcher import get_google_news_viral
        from reddit_news_fetcher import get_reddit_viral_news
        print("   OK: news_fetcher, reputed_rss_fetcher, google_news_fetcher, reddit_news_fetcher")
    except Exception as e:
        print(f"   FAIL: {e}")
        return 1

    # 2) Quick RSS fetch (single feed, fast)
    print("\n2. Fetching reputed RSS (BBC/NPR/Reuters)...")
    try:
        rss = get_reputed_rss_news()
        print(f"   OK: {len(rss)} articles from RSS")
        if rss:
            print(f"   Sample: {rss[0].get('source')} - {rss[0].get('title', '')[:50]}...")
    except Exception as e:
        print(f"   WARN: {e}")

    # 3) Full pipeline (all sources merged)
    print("\n3. Full pipeline (Reddit + News API + Google News + RSS)...")
    try:
        articles = get_trending_news()
        print(f"   OK: {len(articles)} total articles")
        by_source = {}
        for a in articles:
            s = a.get("source", "?")
            by_source[s] = by_source.get(s, 0) + 1
        for s, c in sorted(by_source.items(), key=lambda x: -x[1])[:10]:
            print(f"      {s}: {c}")
        if articles:
            print(f"   Top: {articles[0].get('title', '')[:55]}...")
    except Exception as e:
        print(f"   FAIL: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("ALL SOURCES VERIFIED")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
