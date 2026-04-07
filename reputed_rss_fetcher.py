#!/usr/bin/env python3
"""
Fetch breaking news from reputed, publicly available, verified sources via RSS.
Sources: BBC News, NPR, Reuters (official public RSS feeds).
"""

import requests
from datetime import datetime
from urllib.parse import urljoin

# Public RSS feeds from verified outlets (no API key required).
# If a feed fails (e.g. DNS/blocked), others still run.
# Public RSS only. Reuters feeds.reuters.com often fails DNS / deprecated; BBC retired some regional business paths (404).
REPUTED_RSS_FEEDS = [
    {"url": "https://feeds.bbci.co.uk/news/rss.xml", "source": "BBC News"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "https://feeds.npr.org/1001/rss.xml", "source": "NPR"},
    {"url": "https://www.marketwatch.com/rss/topstories", "source": "MarketWatch"},
    {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "source": "WSJ Markets"},
    # Legacy Reuters (many networks block or NXDOMAIN feeds.reuters.com); keep last as optional retry
    {"url": "https://feeds.reuters.com/reuters/topNews", "source": "Reuters"},
]

# US / Europe business & markets (used when finance_focus=True)
REPUTED_RSS_FEEDS_FINANCE = [
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "source": "BBC Business"},
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "source": "CNBC Top News"},
    {"url": "https://www.cnbc.com/id/15839135/device/rss/rss.html", "source": "CNBC Market News"},
    {"url": "https://www.marketwatch.com/rss/topstories", "source": "MarketWatch"},
    {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "source": "WSJ Markets"},
    {"url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "source": "WSJ US Business"},
]

USER_AGENT = "NewsAggregator/1.0 (Educational; RSS reader)"


def _parse_rss_with_feedparser(xml_text, source_name, feed_url):
    """Parse RSS/Atom XML using feedparser. Returns list of article dicts."""
    try:
        import feedparser
    except ImportError:
        return _parse_rss_stdlib(xml_text, source_name, feed_url)

    parsed = feedparser.parse(xml_text)
    articles = []
    for entry in parsed.get("entries", [])[:15]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        # Description/summary
        summary = entry.get("summary") or entry.get("description", {}).get("value", "") if isinstance(entry.get("description"), dict) else (entry.get("description") or "")
        if isinstance(summary, str):
            desc = summary[:500] if summary else title
        else:
            desc = title
        # Published date
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub:
            try:
                from time import mktime
                pub_dt = datetime.fromtimestamp(mktime(pub))
                published_at = pub_dt.isoformat()
            except Exception:
                # Do not use "now" — that bypasses NEWS_MAX_AGE_HOURS and lets old feed items look fresh.
                published_at = ""
        else:
            published_at = ""
        articles.append({
            "title": title,
            "description": desc,
            "url": link,
            "publishedAt": published_at,
            "source": source_name,
            "engagement": 60,
            "score": 60,
        })
    return articles


def _parse_rss_stdlib(xml_text, source_name, feed_url):
    """Fallback: parse RSS 2.0 with xml.etree (no feedparser)."""
    import xml.etree.ElementTree as ET
    articles = []
    try:
        root = ET.fromstring(xml_text)
        # RSS 2.0: channel > item; Atom: feed > entry
        items = list(root.iter("item")) or list(root.iter("{http://www.w3.org/2005/Atom}entry"))
        for item in items[:15]:
            title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
            link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
            title = (title_el.text or "").strip() if title_el is not None and title_el.text else ""
            link = ""
            if link_el is not None:
                link = (link_el.get("href") or link_el.text or "").strip()
            if not title:
                continue
            if not link and link_el is not None:
                link = link_el.text or ""
            desc_el = item.find("description") or item.find("summary") or item.find("{http://www.w3.org/2005/Atom}summary")
            desc = (desc_el.text or title)[:500] if desc_el is not None else title
            pub_el = item.find("pubDate") or item.find("published") or item.find("updated") or item.find("{http://www.w3.org/2005/Atom}published") or item.find("{http://www.w3.org/2005/Atom}updated")
            published_at = ""
            if pub_el is not None and getattr(pub_el, "text", None):
                try:
                    from email.utils import parsedate_to_datetime
                    published_at = parsedate_to_datetime(pub_el.text).isoformat()
                except Exception:
                    try:
                        published_at = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00")).isoformat()
                    except Exception:
                        pass
            articles.append({
                "title": title,
                "description": desc,
                "url": link or feed_url,
                "publishedAt": published_at,
                "source": source_name,
                "engagement": 60,
                "score": 60,
            })
    except Exception:
        pass
    return articles


def get_reputed_rss_news(finance_focus: bool = False):
    """
    Fetch headlines from BBC, NPR, Reuters (and similar) via public RSS.
    When finance_focus=True, prefer business/markets feeds (US/Europe pipeline).
    Returns list of article dicts in same format as news_fetcher (title, description, url, source, engagement, score).
    """
    feeds = REPUTED_RSS_FEEDS_FINANCE if finance_focus else REPUTED_RSS_FEEDS
    label = "business/markets RSS" if finance_focus else "BBC, NPR, Reuters"
    print(f"Fetching from reputed RSS sources ({label})...")
    all_articles = []
    seen_titles = set()

    for feed in feeds:
        url = feed["url"]
        source_name = feed["source"]
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12)
            r.raise_for_status()
            xml_text = r.text
        except Exception as e:
            print(f"  RSS fetch {source_name}: {e}")
            continue
        try:
            articles = _parse_rss_with_feedparser(xml_text, source_name, url)
            for a in articles:
                key = (a["title"][:80].lower() if a.get("title") else "")
                if key and key not in seen_titles:
                    seen_titles.add(key)
                    all_articles.append(a)
        except Exception as e:
            print(f"  RSS parse {source_name}: {e}")

    if all_articles:
        print(f"Found {len(all_articles)} articles from reputed RSS ({label}).")
    return all_articles
