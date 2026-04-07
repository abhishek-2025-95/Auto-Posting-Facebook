#!/usr/bin/env python3
"""
Enhanced news diversity system to prevent repeated content
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from news_fetcher import get_trending_news

try:
    from config import NEWS_MAX_AGE_HOURS as _NEWS_MAX_AGE_HOURS
    from config import NEWS_RELAXED_MAX_AGE_HOURS as _NEWS_RELAXED_MAX_AGE_HOURS
except ImportError:
    _NEWS_MAX_AGE_HOURS = 8.0
    _NEWS_RELAXED_MAX_AGE_HOURS = 48.0


def _published_date_from_url(url: str):
    """
    Best-effort date from URL path segments like /2026/03/30/ (CNBC, many news sites).
    Returns timezone-aware UTC datetime at noon, or None.
    """
    if not url or not isinstance(url, str):
        return None
    m = re.search(r"/(20[2-9]\d)/(\d{2})/(\d{2})/", url)
    if not m:
        return None
    try:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(y, mo, d, 12, 0, 0, tzinfo=timezone.utc)
    except ValueError:
        return None


def _article_published_dt_utc(article):
    """Parse publish time as timezone-aware UTC, or None if missing/unparseable. Falls back to date embedded in URL."""
    raw = article.get("publishedAt") or article.get("pubDate") or article.get("published_at") or ""
    dt = None
    if raw and isinstance(raw, str):
        s = raw.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except (ValueError, TypeError):
            s2 = raw.replace("Z", "").strip()[:19]
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(s2[:19], fmt)
                    break
                except (ValueError, TypeError):
                    continue
    dt_url = _published_date_from_url((article.get("url") or article.get("link") or "").strip())
    if dt is None:
        return dt_url
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # If feed timestamp disagrees with URL path date, use the older (stricter) instant so stale items stay out.
    if dt_url is not None:
        dt = min(dt, dt_url)
    return dt


def _article_published_within_hours(article, hours: float) -> bool:
    """True if article has a parseable time and it is at most ``hours`` old (UTC), not in the future beyond skew."""
    dt = _article_published_dt_utc(article)
    if dt is None:
        return False
    now = datetime.now(timezone.utc)
    delta = (now - dt).total_seconds()
    if delta < -120:
        return False
    return delta <= float(hours) * 3600.0 + 60.0


def _filter_reputed_and_recent(articles, max_age_hours: float):
    """Keep only items from ``news_fetcher`` reputed desks and published within ``max_age_hours``."""
    from news_fetcher import _source_is_reputed_finance_outlet

    out = []
    for a in articles:
        if not _source_is_reputed_finance_outlet(a.get("source", "")):
            continue
        if not _article_published_within_hours(a, max_age_hours):
            continue
        out.append(a)
    return out

# File to track posted articles (set POSTED_ARTICLES_FILE in .env for second page, e.g. posted_articles_india.json)
POSTED_ARTICLES_FILE = os.environ.get("POSTED_ARTICLES_FILE", "posted_articles.json")
# How many most recent *local* records to check for duplicates (title/URL/similarity). Use 25+ to avoid reposting same news.
POSTED_ARTICLES_DUPLICATE_CHECK_COUNT = 25

def load_posted_articles():
    """Load list of previously posted articles"""
    if os.path.exists(POSTED_ARTICLES_FILE):
        try:
            with open(POSTED_ARTICLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_posted_article(article):
    """Save article to prevent repetition"""
    posted_articles = load_posted_articles()
    
    # Add new article
    article_record = {
        'title': article['title'],
        'url': article.get('url', ''),
        'posted_at': datetime.now().isoformat(),
        'source': article.get('source', '')
    }
    
    posted_articles.append(article_record)
    
    # Keep only last 50 articles to prevent file from growing too large
    if len(posted_articles) > 50:
        posted_articles = posted_articles[-50:]
    
    with open(POSTED_ARTICLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(posted_articles, f, indent=2, ensure_ascii=False)

def is_article_posted(article):
    """Check if article was in the last N local posts (by title similarity or URL). Uses last POSTED_ARTICLES_DUPLICATE_CHECK_COUNT records."""
    posted_articles = load_posted_articles()
    check_count = POSTED_ARTICLES_DUPLICATE_CHECK_COUNT
    recent = posted_articles[-check_count:] if len(posted_articles) > check_count else posted_articles
    title_lower = (article.get('title') or '').lower()
    url = (article.get('url') or '').strip()

    for posted in recent:
        posted_title_lower = (posted.get('title') or '').lower()
        posted_url = (posted.get('url') or '').strip()
        # Same URL = same story (strongest signal)
        if url and posted_url and url == posted_url:
            return True
        # Exact title match
        if title_lower and title_lower == posted_title_lower:
            return True
        # High title similarity (same story, different headline)
        if title_lower and posted_title_lower and calculate_similarity(title_lower, posted_title_lower) > 0.8:
            return True
    return False

def calculate_similarity(str1, str2):
    """Calculate similarity between two strings"""
    words1 = set(str1.split())
    words2 = set(str2.split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def _normalize_for_compare(text):
    """Normalize text for duplicate comparison: strip, collapse whitespace, lower."""
    if not text or not isinstance(text, str):
        return ""
    return " ".join((text or "").split()).strip().lower()


def is_duplicate_on_facebook(text, limit=50, similarity_threshold=0.65):
    """
    Check if the given text (e.g. caption or headline) is already on the Facebook page.
    Fetches the last `limit` posts and returns True if any post message is an exact match
    (after normalizing) or has word similarity >= similarity_threshold.
    Returns False on API error or if no duplicate is found.
    """
    if not text or not str(text).strip():
        return False
    try:
        from facebook_api import get_recent_posts
    except ImportError:
        print("WARNING: facebook_api not available; skipping Facebook duplicate check.")
        return False
    posts = get_recent_posts(limit=limit)
    if not posts:
        print("WARNING: No recent posts fetched from Facebook; duplicate check skipped (post may still go through).")
        return False
    norm_new = _normalize_for_compare(text)
    if not norm_new:
        return False
    for p in posts:
        msg = (p.get("message") or "").strip()
        if not msg:
            continue
        norm_msg = _normalize_for_compare(msg)
        if norm_msg == norm_new:
            return True
        if calculate_similarity(norm_new, norm_msg) >= similarity_threshold:
            return True
    return False


def _parse_article_date(article):
    """Return a datetime for sorting; newest first. Unparseable/missing -> datetime.min so they sort last."""
    dt = _article_published_dt_utc(article)
    if dt is not None:
        return dt.replace(tzinfo=None)
    raw = article.get('publishedAt') or article.get('pubDate') or article.get('published_at') or ''
    if not raw or not isinstance(raw, str):
        return datetime.min
    s = raw.strip().replace('Z', '')[:19]
    # ISO-style: 2025-03-06T12:00:00 or 2025-03-06
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        pass
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s[:19], fmt)
        except (ValueError, TypeError):
            continue
    return datetime.min


def _article_is_us_or_uk(article):
    """
    True if the item is plausibly US or UK financial / macro news.
    Prefer News API ``(US)`` / ``(GB)`` source tags; otherwise require US/UK keywords in title+description.
    """
    src = (article.get("source") or "").upper()
    if "(US)" in src or "(GB)" in src or "(UK)" in src:
        return True
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    uk_hits = (
        "united kingdom",
        "u.k.",
        "britain",
        "british",
        "london",
        "bank of england",
        " uk",
        "uk ",
        "ftse",
        "chancellor",
        "sterling",
        "gbp",
    )
    us_hits = (
        "u.s.",
        "united states",
        "america",
        "washington",
        "fed ",
        "federal reserve",
        "wall street",
        "treasury",
        "nasdaq",
        "s&p",
        "nyse",
        " sec",
    )
    return any(h in text for h in uk_hits) or any(h in text for h in us_hits)


def get_fresh_viral_news_us_uk():
    """Like ``get_fresh_viral_news`` but only considers articles tied to US or UK (see ``_article_is_us_or_uk``)."""
    print(
        "Fetching FRESH viral news (reputed, %.1fh / %.1fh, US/UK scope, avoiding repeats)..."
        % (_NEWS_MAX_AGE_HOURS, _NEWS_RELAXED_MAX_AGE_HOURS)
    )
    article_list = get_trending_news()
    if not article_list:
        print("No articles found")
        return None
    filtered = _filter_reputed_and_recent(article_list, _NEWS_MAX_AGE_HOURS)
    if not filtered and _NEWS_RELAXED_MAX_AGE_HOURS > _NEWS_MAX_AGE_HOURS:
        filtered = _filter_reputed_and_recent(article_list, _NEWS_RELAXED_MAX_AGE_HOURS)
        if filtered:
            print(
                f"[NEWS] Nothing in last {_NEWS_MAX_AGE_HOURS:g}h; using reputed items from last "
                f"{_NEWS_RELAXED_MAX_AGE_HOURS:g}h (US/UK filter next)."
            )
    if not filtered:
        print(
            f"[NEWS] No reputed articles in the last {_NEWS_RELAXED_MAX_AGE_HOURS:g}h (US/UK pipeline). "
            "Widen NEWS_RELAXED_MAX_AGE_HOURS or check feeds."
        )
        return None
    us_uk_pool = [a for a in filtered if _article_is_us_or_uk(a)]
    if not us_uk_pool:
        print("[NEWS] No US/UK-tagged or US/UK-keyword articles in reputed+recent pool; using full filtered pool.")
        us_uk_pool = filtered

    fresh_articles = []
    for article in us_uk_pool:
        if not is_article_posted(article):
            fresh_articles.append(article)
        else:
            print(f"SKIPPING REPEAT: {article['title'][:50]}...")

    if not fresh_articles:
        print("WARNING: All US/UK-scoped articles have been posted before!")
        return None

    fresh_articles.sort(key=_parse_article_date, reverse=True)
    selected = fresh_articles[0]
    print(f"Selected most recent (US/UK): {selected.get('title', '')[:60]}...")
    return selected


def get_fresh_viral_news():
    """Get fresh viral news that hasn't been posted before. Always picks the most recent article from the fresh list."""
    print(
        "Fetching FRESH viral news (reputed sources, last %.1fh strict / %.1fh max, avoiding repeats)..."
        % (_NEWS_MAX_AGE_HOURS, _NEWS_RELAXED_MAX_AGE_HOURS)
    )

    # Get trending news
    article_list = get_trending_news()

    if not article_list:
        print("No articles found")
        return None

    filtered = _filter_reputed_and_recent(article_list, _NEWS_MAX_AGE_HOURS)
    if not filtered and _NEWS_RELAXED_MAX_AGE_HOURS > _NEWS_MAX_AGE_HOURS:
        filtered = _filter_reputed_and_recent(article_list, _NEWS_RELAXED_MAX_AGE_HOURS)
        if filtered:
            print(
                f"[NEWS] Nothing in last {_NEWS_MAX_AGE_HOURS:g}h; using reputed items from last "
                f"{_NEWS_RELAXED_MAX_AGE_HOURS:g}h (newest wins)."
            )
    if not filtered:
        print(
            f"[NEWS] No articles from reputed outlets in the last {_NEWS_RELAXED_MAX_AGE_HOURS:g}h. "
            "Check feeds, NEWS_API_KEY, or raise NEWS_RELAXED_MAX_AGE_HOURS in .env."
        )
        return None

    # Filter out already posted articles
    fresh_articles = []
    for article in filtered:
        if not is_article_posted(article):
            fresh_articles.append(article)
        else:
            print(f"SKIPPING REPEAT: {article['title'][:50]}...")
    
    if not fresh_articles:
        print("WARNING: All articles have been posted before!")
        print(
            f"[NEWS] {len(filtered)} reputed item(s) match the age window but every URL/title is already in "
            "posted_articles.json - not a feed outage. New RSS/Newsdata headlines will post again when they arrive."
        )
        print("Skipping this cycle to avoid duplicate posts.")
        return None
    
    print(f"Found {len(fresh_articles)} fresh articles")
    
    # Select the most recent (latest) from fresh articles
    if fresh_articles:
        fresh_articles.sort(key=_parse_article_date, reverse=True)
        selected = fresh_articles[0]
        print(f"Selected most recent: {selected.get('title', '')[:60]}...")
        return selected
    
    return None


def pick_freshest_postable_article():
    """
    Single entry for posting pipelines: newest reputed story within ``NEWS_MAX_AGE_HOURS`` that has not been posted.

    Does **not** fall back to an unfiltered ``get_trending_news`` + viral-score pick (that path could surface stale items).
    """
    return get_fresh_viral_news()


def create_diverse_post():
    """Create a post with fresh, diverse content"""
    print("Creating DIVERSE post...")
    print("=" * 50)
    
    try:
        # Get fresh viral news
        viral_article = get_fresh_viral_news()
        
        if not viral_article:
            print("No fresh viral content found")
            return False
        
        print(f"Selected FRESH content: {viral_article['title']}")
        
        # Save to prevent future repetition
        save_posted_article(viral_article)
        
        return viral_article
        
    except Exception as e:
        print(f"Error creating diverse post: {e}")
        return False

if __name__ == "__main__":
    # Test the diversity system
    print("Testing news diversity system...")
    fresh_article = create_diverse_post()
    
    if fresh_article:
        print(f"SUCCESS: Fresh article selected - {fresh_article['title']}")
    else:
        print("FAILED: No fresh content available")

