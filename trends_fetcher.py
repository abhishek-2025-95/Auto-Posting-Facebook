# trends_fetcher.py - Fetch US Google Trends topics (last 12-24h)
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import requests
import re
import google.generativeai as genai
from config import GEMINI_API_KEY


def clean_topic(s: str) -> str:
    if not s:
        return s
    return re.sub(r"\s+", " ", s).strip()


def get_us_trending_topics(max_items: int = 8):
    """
    Returns a list of dicts similar to news_fetcher output:
    { 'title', 'description', 'url', 'publishedAt', 'source' }
    Uses Google Trends daily trending searches for US.
    """
    print("Fetching US Google Trends...")

    pytrends = TrendReq(hl='en-US', tz=360)

    topics = []
    now = datetime.now()

    # Configure Gemini once (for fallback)
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

    # Try direct Google realtime trends endpoint first
    try:
        realtime_url = (
            "https://trends.google.com/trends/api/realtimetrends"
            "?hl=en-US&tz=0&cat=all&fi=0&fs=0&geo=US&ri=300&rs=20&gprop="
        )
        r = requests.get(realtime_url, timeout=15)
        r.raise_for_status()
        raw = r.text
        # Remove XSSI prefix ")]}'\n"
        if raw.startswith(")]}'"):
            raw = raw.split('\n', 1)[1]
        import json as _json
        data = _json.loads(raw)
        stories = (data.get('storySummaries', {}) or {}).get('trendingStories', [])
        for s in stories[:max_items]:
            title = clean_topic(s.get('title'))
            if not title and s.get('entityNames'):
                title = clean_topic(s['entityNames'][0])
            if not title:
                continue
            # pick the first article url if present
            url = None
            for art in s.get('articles', []):
                if art.get('url'):
                    url = art['url']
                    break
            topics.append({
                'title': title,
                'description': f'Real-time trending in the US: {title}',
                'url': url or f'https://trends.google.com/trends/trendingsearches/realtime?geo=US&q={title}',
                'publishedAt': now.isoformat(),
                'source': 'GoogleRealtimeEndpoint'
            })
        if topics:
            print(f"Found {len(topics)} US realtime topics (direct endpoint)")
            return topics
    except Exception:
        pass

    # Try realtime via pytrends
    # Try realtime first (US)
    try:
        rtdf = pytrends.trending_searches_realtime(pn='US', cat='all', count=50)
        for _, row in rtdf.head(max_items).iterrows():
            title = clean_topic(str(row.get('title') or row.get('query') or row.get(0)))
            if not title:
                continue
            topics.append({
                'title': title,
                'description': f'Real-time trending in the US: {title}',
                'url': f'https://trends.google.com/trends/trendingsearches/realtime?geo=US&q={title}',
                'publishedAt': now.isoformat(),
                'source': 'GoogleTrendsRealtime'
            })
        if topics:
            print(f"Found {len(topics)} US realtime topics")
            return topics
    except Exception:
        # Fallback to daily trending
        try:
            ddf = pytrends.trending_searches(pn='united_states')
            for _, row in ddf.head(max_items).iterrows():
                topic = clean_topic(str(row[0]))
                if not topic:
                    continue
                topics.append({
                    'title': topic,
                    'description': f'Trending in the US: {topic}',
                    'url': f'https://trends.google.com/trends/trendingsearches/daily?geo=US&q={topic}',
                    'publishedAt': now.isoformat(),
                    'source': 'GoogleTrendsDaily'
                })
            if topics:
                print(f"Found {len(topics)} US daily topics")
                return topics
        except Exception:
            pass

    # Final fallback: ask Gemini to propose top US trends (heuristic)
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        fallback_prompt = (
            "List the top 8 breaking or trending topics in the United States from the last 12 hours. "
            "Return only JSON array with objects: {title, description}. No extra text."
        )
        resp = model.generate_content(fallback_prompt)
        txt = (resp.text or '').strip()
        if txt.startswith('```'):
            txt = txt.split('\n', 1)[-1]
            if txt.endswith('```'):
                txt = txt[:-3]
        import json as _json
        items = _json.loads(txt)
        for it in items[:max_items]:
            title = clean_topic(it.get('title'))
            desc = it.get('description') or f'Trending in the US: {title}'
            if not title:
                continue
            topics.append({
                'title': title,
                'description': desc,
                'url': f'https://trends.google.com/?geo=US&q={title}',
                'publishedAt': now.isoformat(),
                'source': 'GeminiHeuristic'
            })
    except Exception:
        pass

    print(f"Found {len(topics)} US trending topics")
    return topics


def select_top_trend(topics):
    """Pick the first topic as the most viral (simple heuristic)."""
    return topics[0] if topics else None
