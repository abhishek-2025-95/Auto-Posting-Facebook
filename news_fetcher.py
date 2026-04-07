# news_fetcher.py - Fetch trending news and select viral topics (no Gemini required; select by engagement)
import warnings
import re
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin
from config import NEWS_API_KEY, NEWS_LANGUAGE, NEWS_COUNTRIES, NEWS_HOURS_BACK
try:
    from config import NEWS_MAX_COUNTRIES, NEWS_MAX_ARTICLES_PER_COUNTRY, NEWS_POOL_SIZE
except ImportError:
    NEWS_MAX_COUNTRIES = 10
    NEWS_MAX_ARTICLES_PER_COUNTRY = 20
    NEWS_POOL_SIZE = 35
try:
    from config import NEWS_MARKETS_US_EUROPE_ONLY, NEWSDATA_CATEGORY
except ImportError:
    NEWS_MARKETS_US_EUROPE_ONLY = False
    NEWSDATA_CATEGORY = ""
try:
    from config import NEWS_BREAKING_FINANCE_REPUTED_ONLY, NEWS_REQUIRE_BREAKING_HEADLINE
except ImportError:
    NEWS_BREAKING_FINANCE_REPUTED_ONLY = False
    NEWS_REQUIRE_BREAKING_HEADLINE = True

# Premier: wires + leading business desks (substring match on `source` field from Newsdata or RSS label).
REPUTED_FINANCE_OUTLETS_PREMIER = (
    "reuters",
    "bloomberg",
    "cnbc",
    "bbc",
    "financial times",
    "ft.com",
    "the wall street journal",
    "wsj",
    "marketwatch",
    "barron",
    "ap news",
    "associated press",
    "the economist",
    "morningstar",
    "financial post",
    "npr",
    "dow jones",
)

# Secondary (opt-in via NEWS_REPUTED_PREMIER_ONLY=0): aggregators and trade press.
REPUTED_FINANCE_OUTLETS_SECONDARY = (
    "fortune",
    "forbes",
    "nasdaq",
    "yahoo finance",
    "investing.com",
    "seeking alpha",
    "business insider",
    "the street",
)

# Back-compat name: premier + secondary (used when premier-only mode is off).
REPUTED_FINANCE_OUTLETS = REPUTED_FINANCE_OUTLETS_PREMIER + REPUTED_FINANCE_OUTLETS_SECONDARY


def _reputed_outlet_needles():
    try:
        from config import NEWS_REPUTED_PREMIER_ONLY

        if NEWS_REPUTED_PREMIER_ONLY:
            return REPUTED_FINANCE_OUTLETS_PREMIER
    except ImportError:
        pass
    return REPUTED_FINANCE_OUTLETS


def _source_is_reputed_finance_outlet(source: str) -> bool:
    s = (source or "").lower()
    if not s.strip():
        return False
    if "reddit" in s or "google news" in s:
        return False
    return any(x in s for x in _reputed_outlet_needles())


def _headline_is_breaking_finance(title: str, desc: str) -> bool:
    """Breaking-style or clearly market-moving headline (US/Europe markets context)."""
    t = f"{title} {desc or ''}".lower()
    if not t.strip():
        return False
    if re.search(
        r"\b(breaking|just in|urgent|developing|flash\b|live\s*updates|market\s*alert|"
        r"latest\s*on\s*the\s*markets|markets\s*wrap)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(stocks?|stock\s+market|s\s*&\s*p|s&p\s*500|nasdaq|dow(\s+jones)?|ftse|dax|cac)\b"
        r".{0,90}\b(plunge|soar|surge|rout|crash|skyrocket|tumble|record\s+(high|low|gain|loss|close))\b",
        t,
    ):
        return True
    if re.search(
        r"\b(plunge|soar|surge|rout|crash|tumble|skyrocket)\b"
        r".{0,90}\b(stocks?|market|nasdaq|s&p|dow|ftse|dax|cac)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(fed|federal\s+reserve|ecb|bank\s+of\s+england)\b"
        r".{0,80}\b(hike|cut|hold|slash|raise|pause|decision|meeting|votes)\b",
        t,
    ):
        return True
    # Substantive macro / economy + markets (calmer headlines, still on-brief for finance page)
    if re.search(
        r"\b(gdp|gross\s+domestic|inflation|consumer\s+prices|cpi|ppi|pce|deflator|"
        r"unemployment|jobless|payrolls?|non-?farm|wages|retail\s+sales|pmi|ism|"
        r"industrial\s+production|housing\s+starts|mortgage|trade\s+(deficit|surplus)|"
        r"current\s+account|eurozone|recession|economic\s+growth|fiscal|budget|"
        r"earnings|guidance|profit\s+warning|dividend|buyback|merger|acquisition|ipo)\b",
        t,
    ) and re.search(
        r"\b(market|markets|stock|stocks|share|equity|bond|yield|dollar|euro|pound|sterling|"
        r"investor|trading|s\s*&\s*p|s&p|nasdaq|dow|ftse|dax|cac|economy|economic|"
        r"fed|ecb|boe|central\s+bank|wall\s+street|treasury|company|bank|corporate)\b",
        t,
    ):
        return True
    return False


def _article_passes_breaking_reputed(article: dict) -> bool:
    """Reputed outlet + US/Europe markets + optional breaking headline."""
    if not _source_is_reputed_finance_outlet(article.get("source", "")):
        return False
    if not article_matches_markets_us_europe(article, geo_required=False):
        return False
    if NEWS_REQUIRE_BREAKING_HEADLINE and not _headline_is_breaking_finance(
        article.get("title") or "", article.get("description") or ""
    ):
        return False
    return True

# US / EU country tags from Newsdata source field, e.g. "CNN (US)"
_US_EU_SOURCE_CODES = frozenset(
    "US GB UK DE FR IT ES NL IE BE AT PL PT CH SE NO DK FI EU GR CZ RO HU".split()
)

# Title/description: economy & markets (US / Europe angle)
_FINANCE_KEYWORDS = frozenset(
    """
    stock market stocks shares equity equities nasdaq dow s&p 500 ftse dax cac
    fed federal reserve fomc interest rate rates hike cut ecb european central bank
    bank of england boe bundesbank inflation cpi pmi gdp recession earnings revenue
    profit forecast guidance merger acquisition m&a ipo bond treasury yield yields
    forex dollar euro pound sterling commodity commodities oil brent wti gold silver
    trader investor wall street main street sec regulation fine lawsuit settlement
    debt deficit budget fiscal stimulus trade tariff sanctions export import
    unemployment jobs report payroll retail sales consumer mortgage housing commercial real estate
    yellen powell lagarde bitcoin etf crypto exchange bank banking lender credit
    """.split()
)

_FINANCE_SOURCE_SUBSTR = (
    "bloomberg", "reuters", "cnbc", "wsj", "wall street", "marketwatch", "financial times",
    "ft.com", "economist", "fool", "seeking", "barron", "investing.com", "yahoo finance",
    "nasdaq", "eurostat", "ecb", "federal reserve", "sec", "treasury", "morningstar",
    "kitco", "business insider", "fortune", "forbes",
)

# Strong “not our beat” when no finance signal
_EXCLUDE_IF_NO_FINANCE = frozenset(
    """
    super bowl nfl nba nhl world cup premier league uefa champions league
    oscars grammy emmys celebrity red carpet halftime touchdown
    """.split()
)

# Avoid 2-letter tokens (false positives in unrelated words)
_US_EU_GEO_TERMS = frozenset(
    """
    u.s. usa america american united states washington congress senate white house
    europe european eurozone euro area germany german france french italy italian
    spain spanish uk britain british england scotland wales ireland dutch netherlands
    belgium swiss switzerland austria polish poland portugal sweden norwegian norway
    denmark finland finnish greek athens brussels
    wall street nasdaq nyse london frankfurt paris madrid dublin vienna stock exchange
    ecb fed federal reserve euro dollar pound sterling
    """.split()
)


def article_matches_markets_us_europe(article: dict, *, geo_required: bool = True) -> bool:
    """
    True if article is plausibly about US/European financial markets or economy.
    Uses keywords + source name; optional geographic hint when geo_required.
    """
    title = (article.get("title") or "").lower()
    desc = (article.get("description") or article.get("content") or "").lower()
    text = f"{title} {desc}"
    src = (article.get("source") or "").lower()

    if any(s in src for s in _FINANCE_SOURCE_SUBSTR):
        return True

    hits = sum(1 for kw in _FINANCE_KEYWORDS if kw in text)
    if hits >= 1:
        if not geo_required:
            return True
        # Geographic relevance: country tag, or US/Europe terms in text
        for code in _US_EU_SOURCE_CODES:
            if f"({code.lower()})" in src or f"({code})" in article.get("source", ""):
                return True
        if any(g in text for g in _US_EU_GEO_TERMS):
            return True
        # Finance-heavy headlines often imply US markets (e.g. "S&P 500")
        if hits >= 2:
            return True
        return False

    # No finance keywords: drop if clearly sports/entertainment
    if any(ex in text for ex in _EXCLUDE_IF_NO_FINANCE):
        return False

    return False

def _title_similar(a, b):
    """True if two article titles are very similar (avoid duplicate stories)."""
    t1 = (a.get('title') or '').lower()
    t2 = (b.get('title') or '').lower()
    if not t1 or not t2:
        return False
    w1, w2 = set(t1.split()), set(t2.split())
    if not w1 or not w2:
        return False
    return len(w1 & w2) / len(w1 | w2) > 0.6


def get_news_api_us_europe():
    """Fetch latest headlines from News API (newsdata.io) for US + UK + Europe (config NEWS_COUNTRIES)."""
    countries = getattr(__import__('config', fromlist=['NEWS_COUNTRIES']), 'NEWS_COUNTRIES', ['us', 'gb', 'de'])
    api_key = getattr(__import__('config', fromlist=['NEWS_API_KEY']), 'NEWS_API_KEY', None)
    lang = getattr(__import__('config', fromlist=['NEWS_LANGUAGE']), 'NEWS_LANGUAGE', 'en')
    max_countries = getattr(__import__('config', fromlist=['NEWS_MAX_COUNTRIES']), 'NEWS_MAX_COUNTRIES', 10)
    per_country = getattr(__import__('config', fromlist=['NEWS_MAX_ARTICLES_PER_COUNTRY']), 'NEWS_MAX_ARTICLES_PER_COUNTRY', 20)
    if not api_key:
        return []
    url = "https://newsdata.io/api/1/latest"
    merged = []
    seen_titles = set()
    nd_cat = getattr(__import__("config", fromlist=["NEWSDATA_CATEGORY"]), "NEWSDATA_CATEGORY", "") or ""
    for country in countries[:max_countries]:
        try:
            params = {"apikey": api_key, "language": lang, "country": country}
            if nd_cat:
                params["category"] = nd_cat
            r = requests.get(url, params=params, timeout=14)
            r.raise_for_status()
            results = r.json().get('results', [])
            for article in results[:per_country]:
                title = article.get('title') or article.get('title_full') or ''
                link = article.get('link') or article.get('url') or ''
                desc = article.get('description') or article.get('content') or title
                source = article.get('source_id') or article.get('source') or 'Unknown'
                pub = article.get('pubDate') or article.get('published_at') or ''
                if not title or not link:
                    continue
                key = title[:80].lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                merged.append({
                    'title': title,
                    'description': desc[:500] if desc else title,
                    'url': link,
                    'publishedAt': pub,
                    'source': f"{source} ({country.upper()})",
                    'engagement': 50,
                    'score': 50,
                })
        except Exception as e:
            print(f"News API {country}: {e}")
            continue
    if merged:
        extra = f", category={nd_cat}" if nd_cat else ""
        print(f"Found {len(merged)} headlines from News API (US, UK & Europe{extra}).")
    return merged


def _is_bihar_article(article):
    """True if the article is about Bihar (title or description mentions Bihar/Patna)."""
    title = (article.get('title') or '').lower()
    desc = (article.get('description') or article.get('content') or '').lower()
    text = title + ' ' + desc
    return 'bihar' in text or 'patna' in text


def get_bihar_gov_news():
    """
    Fetch public announcements / press releases from Government of Bihar sources.
    Tries CM Secretariat news page and Governor's press release page. Returns same article format.
    """
    articles = []
    headers = {'User-Agent': 'BiharPulseBot/1.0 (Educational)'}
    base_cm = "https://cm.bihar.gov.in"
    base_governor = "https://governor.bih.nic.in"

    # Pattern: <a ... href="...">Title</a> or link text
    def extract_links(html, base_url):
        out = []
        for m in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', html, re.I | re.DOTALL):
            href, text = m.group(1).strip(), re.sub(r'\s+', ' ', m.group(2)).strip()
            if not text or len(text) < 10:
                continue
            if href.startswith('#'):
                continue
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            out.append((text[:300], href))
        return out

    urls_to_try = [
        (f"{base_cm}/users/NewsN.aspx", "Govt of Bihar (CM Secretariat)"),
        (f"{base_governor}/document-category/press-release/", "Bihar Raj Bhavan (Press Release)"),
    ]
    for url, source_label in urls_to_try:
        try:
            r = requests.get(url, headers=headers, timeout=12)
            r.raise_for_status()
            html = r.text
            links = extract_links(html, url)
            for title, link in links[:15]:
                if any(skip in title.lower() for skip in ('login', 'register', 'copyright', 'privacy', 'skip', 'menu')):
                    continue
                articles.append({
                    'title': title,
                    'description': title[:500],
                    'url': link,
                    'publishedAt': datetime.now().strftime('%Y-%m-%d'),
                    'source': source_label,
                    'engagement': 60,
                    'score': 60,
                })
            if articles:
                print(f"Bihar gov: found {len(articles)} items from {source_label}.")
                break
        except Exception as e:
            print(f"Bihar gov fetch {url[:50]}: {e}")
            continue

    return articles


def get_news_bihar():
    """
    Fetch Bihar news from ALL sources: News API (India + Bihar filter), Reddit (search + India/Bihar
    subreddits), and Government of Bihar press/announcements. Merges and dedupes; returns same
    article format as get_trending_news. Used for Bihar Pulse pipeline.
    """
    merged = []
    seen_keys = set()

    def _add(article):
        title = (article.get('title') or '').strip()
        if not title or not article.get('url'):
            return
        key = title[:80].lower()
        if key in seen_keys:
            return
        if any(_title_similar(article, m) for m in merged):
            return
        seen_keys.add(key)
        merged.append(article)

    # 1) News API — India, filter to Bihar/Patna
    api_key = getattr(__import__('config', fromlist=['NEWS_API_KEY']), 'NEWS_API_KEY', None)
    if api_key:
        try:
            r = requests.get(
                "https://newsdata.io/api/1/latest",
                params={'apikey': api_key, 'language': 'en', 'country': 'in'},
                timeout=14,
            )
            r.raise_for_status()
            for article in r.json().get('results', []):
                title = article.get('title') or article.get('title_full') or ''
                link = article.get('link') or article.get('url') or ''
                desc = article.get('description') or article.get('content') or title
                source = article.get('source_id') or article.get('source') or 'Unknown'
                pub = article.get('pubDate') or article.get('published_at') or ''
                if not title or not link:
                    continue
                item = {
                    'title': title,
                    'description': (desc or title)[:500],
                    'url': link,
                    'publishedAt': pub,
                    'source': f"{source} (India/Bihar)",
                    'engagement': 50,
                    'score': 50,
                }
                if not _is_bihar_article(item):
                    continue
                _add(item)
        except Exception as e:
            print(f"News API (Bihar): {e}")

    # 2) Reddit — search "Bihar" + r/india, r/bihar, r/patna, etc.
    try:
        from reddit_news_fetcher import get_reddit_bihar_news
        for post in get_reddit_bihar_news():
            _add({
                'title': post['title'],
                'description': post.get('description', post['title'])[:500],
                'url': post['url'],
                'publishedAt': post.get('publishedAt', ''),
                'source': post.get('source', 'Reddit'),
                'engagement': post.get('engagement', 0),
                'score': post.get('score', 0),
            })
    except Exception as e:
        print(f"Reddit Bihar: {e}")

    # 3) Government of Bihar — press releases / public announcements
    for item in get_bihar_gov_news():
        _add(item)

    merged.sort(key=lambda x: x.get('engagement', 0) + x.get('score', 0), reverse=True)
    if merged:
        print(f"Bihar pipeline total: {len(merged)} articles (News API + Reddit + Govt of Bihar).")
    return merged


def get_trending_news():
    """
    Fetch breaking news from Reddit, News API (newsdata.io), Google News, and reputed RSS (BBC, NPR, Reuters).
    Returns a larger pool so duplicate-filtering has more fresh options.

    When NEWS_BREAKING_FINANCE_REPUTED_ONLY: only finance RSS + Newsdata, reputed outlets,
    US/Europe markets, and breaking-style / market-moving headlines (no Reddit/Google).
    """
    if NEWS_BREAKING_FINANCE_REPUTED_ONLY:
        print(
            "[NEWS] Breaking US/EU markets from reputed sources only "
            "(RSS + Newsdata; Reddit/Google off; headline filter on)."
        )
        rss_articles: list = []
        api_articles: list = []
        try:
            from reputed_rss_fetcher import get_reputed_rss_news

            rss_articles = get_reputed_rss_news(finance_focus=True) or []
        except Exception as e:
            print(f"Reputed RSS fetch failed: {e}")
        try:
            api_articles = get_news_api_us_europe()
        except Exception as e:
            print(f"News API: {e}")

        merged: list = []
        seen = set()
        for a in (rss_articles or []) + (api_articles or []):
            if not a.get("title") or not a.get("url"):
                continue
            key = (a.get("title") or "")[:80].lower()
            if key in seen:
                continue
            if not _article_passes_breaking_reputed(a):
                continue
            seen.add(key)
            merged.append(a)

        merged.sort(key=lambda x: x.get("engagement", 0) + x.get("score", 0), reverse=True)
        if not merged:
            print("[NEWS] No articles passed breaking + reputed + markets filter.")
            return get_fallback_news()
        _api_key = (getattr(__import__("config", fromlist=["NEWS_API_KEY"]), "NEWS_API_KEY", None) or "").strip()
        if not _api_key:
            print(
                f"[NEWS] NEWS_API_KEY is empty -- Newsdata.io is off; pool is RSS-only "
                f"({len(rss_articles or [])} raw RSS items -> {len(merged)} after breaking/reputed filter). "
                "Add a key from https://newsdata.io/ to .env to widen the pipeline."
            )
        elif not (api_articles or []):
            print(
                "[NEWS] Newsdata returned 0 articles (check key, quota, NEWSDATA_CATEGORY, or errors above). "
                f"Using RSS-only pool ({len(merged)} items)."
            )
        pool_size = getattr(__import__("config", fromlist=["NEWS_POOL_SIZE"]), "NEWS_POOL_SIZE", 35)
        print(f"[NEWS] Reputed breaking pool: {len(merged)} articles")
        return merged[:pool_size]

    print("Fetching viral trending news from Reddit...")
    try:
        from reddit_news_fetcher import get_reddit_viral_news
        reddit_posts = get_reddit_viral_news()
    except Exception as e:
        print(f"Reddit fetch failed: {e}")
        reddit_posts = []

    # News API US + Europe (newsdata.io)
    api_articles = get_news_api_us_europe()

    # Google News (aggregator of major sources)
    google_articles = []
    try:
        from google_news_fetcher import get_google_news_viral
        raw = get_google_news_viral()
        for a in raw or []:
            google_articles.append({
                'title': a.get('title', ''),
                'description': a.get('description', a.get('title', ''))[:500],
                'url': a.get('url', ''),
                'publishedAt': a.get('publishedAt', ''),
                'source': a.get('source', 'Google News'),
                'engagement': 55,
                'score': 55,
            })
    except Exception as e:
        print(f"Google News fetch failed: {e}")

    # Reputed RSS: BBC, NPR, Reuters (public, verified sources)
    rss_articles = []
    try:
        from reputed_rss_fetcher import get_reputed_rss_news
        rss_articles = get_reputed_rss_news(finance_focus=NEWS_MARKETS_US_EUROPE_ONLY) or []
    except Exception as e:
        print(f"Reputed RSS fetch failed: {e}")

    formatted_articles = []
    for post in (reddit_posts or []):
        formatted_articles.append({
            'title': post['title'],
            'description': post['description'],
            'url': post['url'],
            'publishedAt': post['publishedAt'],
            'source': post['source'],
            'engagement': post.get('engagement', 0),
            'score': post.get('score', 0),
            'comments': post.get('comments', 0),
            'subreddit': post.get('subreddit', ''),
        })

    def _merge_dedup(new_articles):
        for art in new_articles:
            if not art.get('title') or not art.get('url'):
                continue
            if any(_title_similar(art, existing) for existing in formatted_articles):
                continue
            formatted_articles.append(art)

    _merge_dedup(api_articles)
    _merge_dedup(google_articles)
    _merge_dedup(rss_articles)

    # Sort by engagement (Reddit has real scores; others get default 50–60)
    formatted_articles.sort(key=lambda x: x.get('engagement', 0) + x.get('score', 0), reverse=True)

    if NEWS_MARKETS_US_EUROPE_ONLY and formatted_articles:
        before = len(formatted_articles)
        filtered = [a for a in formatted_articles if article_matches_markets_us_europe(a, geo_required=True)]
        if len(filtered) < 5:
            filtered = [a for a in formatted_articles if article_matches_markets_us_europe(a, geo_required=False)]
        formatted_articles = filtered
        print(
            f"[NEWS] US/Europe markets filter: kept {len(formatted_articles)}/{before} "
            f"(NEWS_MARKETS_US_EUROPE_ONLY=1)"
        )

    if not formatted_articles:
        print("No articles found, using fallback...")
        return get_fallback_news()

    pool_size = getattr(__import__('config', fromlist=['NEWS_POOL_SIZE']), 'NEWS_POOL_SIZE', 35)
    print(f"Found {len(formatted_articles)} total (Reddit + News API + Google News + RSS)")
    return formatted_articles[:pool_size]  # Large pool for enormous pipeline, fewer repeats

def get_news_api_fallback():
    """Original News API fallback method"""
    print("Using News API fallback...")
    
    # Calculate time range (last 24 hours for more realistic results)
    to_date = datetime.now()
    from_date = to_date - timedelta(hours=24)
    
    # Newsdata.io latest headlines endpoint
    url = "https://newsdata.io/api/1/latest"
    
    # Enhanced parameters for viral general news (not just financial)
    # Start without keyword filter to get any results, then filter locally
    params = {
        'apikey': NEWS_API_KEY,
        'language': NEWS_LANGUAGE or 'en',
        'country': 'us'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('results', [])
        
        # Filter and format articles with source prioritization
        formatted_articles = []
        
        # Prioritize general news sources over niche financial sources
        def get_source_priority(source):
            """Prioritize general news sources for viral content"""
            general_sources = {
                'CNN': 10, 'BBC': 10, 'Reuters': 10, 'AP': 10, 'NPR': 9,
                'Fox News': 9, 'MSNBC': 9, 'ABC': 8, 'CBS': 8, 'NBC': 8,
                'USA Today': 8, 'Washington Post': 9, 'New York Times': 9,
                'Guardian': 8, 'Politico': 7, 'Bloomberg': 6, 'WSJ': 6,
                'defenseworld': 2, 'financial': 2, 'business': 3
            }
            
            source_lower = source.lower()
            for key, priority in general_sources.items():
                if key.lower() in source_lower:
                    return priority
            return 5  # Default priority
        
        # Helper to parse date safely
        def parse_pubdate(value: str):
            if not value:
                return None
            fmts = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d"
            ]
            for f in fmts:
                try:
                    return datetime.strptime(value, f)
                except Exception:
                    continue
            return None

        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        for article in articles[:30]:  # take more articles for better filtering
            title = article.get('title') or article.get('title_full')
            desc = article.get('description') or article.get('content')
            link = article.get('link') or article.get('url')
            pub_raw = article.get('pubDate') or article.get('published_at') or ''
            pub_dt = parse_pubdate(pub_raw)
            source = (article.get('source_id') or article.get('source') or 'Unknown')
            
            # Apply 24h post-filter and source quality filter
            if title and desc and link and pub_dt and pub_dt >= twenty_four_hours_ago:
                # Calculate source priority
                source_priority = get_source_priority(source)
                
                # Check for viral keywords in title/description
                title_lower = title.lower()
                desc_lower = desc.lower()
                viral_keywords = [
                    'breaking', 'crisis', 'scandal', 'shocking', 'exclusive',
                    'urgent', 'alert', 'emergency', 'outrage', 'controversy',
                    'election', 'politics', 'crime', 'disaster', 'war', 'conflict',
                    'economy', 'inflation', 'recession', 'health', 'covid', 'pandemic',
                    'climate', 'environment', 'technology', 'ai', 'social media',
                    'viral', 'trending', 'hot', 'major', 'huge', 'massive'
                ]
                
                has_viral_keywords = any(keyword in title_lower or keyword in desc_lower for keyword in viral_keywords)
                
                # Include articles from decent sources OR with viral keywords
                if source_priority >= 4 or has_viral_keywords:
                    formatted_articles.append({
                        'title': title,
                        'description': desc,
                        'url': link,
                        'publishedAt': pub_raw,
                        'source': source,
                        'priority': source_priority  # Add priority for sorting
                    })
        
        # Sort by source priority (highest first) and viral keywords
        def get_viral_score(article):
            """Calculate viral potential score based on keywords and source"""
            title_lower = article['title'].lower()
            desc_lower = article['description'].lower()
            
            # Viral keywords that increase score
            viral_keywords = [
                'breaking', 'crisis', 'scandal', 'shocking', 'exclusive',
                'urgent', 'alert', 'emergency', 'outrage', 'controversy',
                'election', 'politics', 'crime', 'disaster', 'war', 'conflict',
                'economy', 'inflation', 'recession', 'health', 'covid', 'pandemic',
                'climate', 'environment', 'technology', 'ai', 'social media',
                'viral', 'trending', 'hot', 'major', 'huge', 'massive'
            ]
            
            keyword_score = sum(1 for keyword in viral_keywords if keyword in title_lower or keyword in desc_lower)
            source_priority = article.get('priority', 5)
            
            return source_priority + keyword_score
        
        # Sort by viral score (highest first)
        formatted_articles.sort(key=get_viral_score, reverse=True)
        
        # Keep top 5 most viral articles
        formatted_articles = formatted_articles[:5]
        
        # Check if we have good quality articles, if not use enhanced fallback
        has_quality_sources = any(article.get('priority', 0) >= 7 for article in formatted_articles)
        has_viral_content = any(
            any(keyword in article['title'].lower() or keyword in article['description'].lower() 
                for keyword in ['breaking', 'crisis', 'scandal', 'urgent', 'shocking', 'exclusive'])
            for article in formatted_articles
        )
        
        if not has_quality_sources and not has_viral_content:
            print("No quality viral content found, using enhanced fallback...")
            return get_fallback_news()
        
        print(f"Found {len(formatted_articles)} trending viral articles (last 24h)")
        
        # Log the sources we found
        if formatted_articles:
            sources = [article['source'] for article in formatted_articles]
            print(f"Sources: {', '.join(sources)}")
        
        return formatted_articles
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        # Fallback to hardcoded viral topics if API fails
        return get_fallback_news()
    except Exception as e:
        print(f"Unexpected error: {e}")
        return get_fallback_news()

def get_fallback_news():
    """Fallback news if API fails (markets/economy slant when NEWS_MARKETS_US_EUROPE_ONLY)."""
    try:
        from config import NEWS_BREAKING_FINANCE_REPUTED_ONLY as _bf
    except ImportError:
        _bf = False
    if _bf:
        return [
            {
                "title": "BREAKING: S&P 500 futures surge as traders weigh Fed and ECB next moves",
                "description": "US and European markets react to central bank signals and Treasury yields.",
                "url": "https://example.com/breaking-markets-1",
                "publishedAt": datetime.now().isoformat(),
                "source": "Reuters",
                "engagement": 55,
                "score": 55,
            },
            {
                "title": "Stocks plunge in volatile session; Nasdaq leads losses",
                "description": "Wall Street sells off amid macro data and earnings guidance.",
                "url": "https://example.com/breaking-markets-2",
                "publishedAt": datetime.now().isoformat(),
                "source": "Bloomberg",
                "engagement": 55,
                "score": 55,
            },
        ]
    try:
        from config import NEWS_MARKETS_US_EUROPE_ONLY as _mkt_fb
    except ImportError:
        _mkt_fb = False
    if _mkt_fb:
        return [
            {
                "title": "Markets Watch Fed Signals as Inflation Data Looms",
                "description": "Investors weigh US rates path and European growth as central banks stay in focus.",
                "url": "https://example.com/fed-markets",
                "publishedAt": datetime.now().isoformat(),
                "source": "Reuters",
                "engagement": 55,
                "score": 55,
            },
            {
                "title": "European Stocks, US Futures Move on ECB and Earnings Outlook",
                "description": "DAX and S&P-linked sentiment shift after macro data and corporate guidance.",
                "url": "https://example.com/eu-us-markets",
                "publishedAt": datetime.now().isoformat(),
                "source": "Bloomberg",
                "engagement": 55,
                "score": 55,
            },
            {
                "title": "Treasury Yields, Euro Steady After Jobs and CPI-Focused Week",
                "description": "Bond and FX markets parse US and euro-area indicators.",
                "url": "https://example.com/bonds-fx",
                "publishedAt": datetime.now().isoformat(),
                "source": "CNBC",
                "engagement": 54,
                "score": 54,
            },
        ]
    return [
        {
            'title': 'BREAKING: Major Data Breach Exposes Millions of Americans',
            'description': 'Shocking security failure leaves personal information vulnerable in what experts call the largest breach of 2024',
            'url': 'https://example.com/tech-breach',
            'publishedAt': datetime.now().isoformat(),
            'source': 'CNN',
            'priority': 10
        },
        {
            'title': 'URGENT: Economic Crisis Deepens as Inflation Hits Record High',
            'description': 'Central banks scramble to address unprecedented economic challenges affecting millions of families',
            'url': 'https://example.com/economy-crisis',
            'publishedAt': datetime.now().isoformat(),
            'source': 'Reuters',
            'priority': 10
        },
        {
            'title': 'EXCLUSIVE: Climate Summit Ends in Major Controversy',
            'description': 'World leaders clash over environmental policies as global temperatures continue to rise dramatically',
            'url': 'https://example.com/climate-summit',
            'publishedAt': datetime.now().isoformat(),
            'source': 'BBC',
            'priority': 10
        },
        {
            'title': 'SHOCKING: New Study Reveals Hidden Health Crisis',
            'description': 'Groundbreaking research exposes concerning trends that could affect millions of Americans',
            'url': 'https://example.com/health-study',
            'publishedAt': datetime.now().isoformat(),
            'source': 'NPR',
            'priority': 9
        },
        {
            'title': 'BREAKING: Major Political Scandal Rocks Washington',
            'description': 'Exclusive investigation reveals shocking details that could change everything',
            'url': 'https://example.com/political-scandal',
            'publishedAt': datetime.now().isoformat(),
            'source': 'Washington Post',
            'priority': 9
        }
    ]

def select_viral_topic(articles):
    """
    Select the most viral topic from the list by engagement/score (no Gemini). Returns first article with highest score.
    """
    if not articles:
        return {
            'title': 'Breaking: Major Development Shakes Markets',
            'description': 'Significant event with far-reaching implications for global economy',
            'url': 'https://example.com/breaking-news',
            'source': 'News Agency',
            'viral_reason': 'High impact breaking news'
        }
    # Sort by engagement + score (same as get_fresh_viral_news)
    best = max(articles, key=lambda x: x.get('score', 0) + x.get('engagement', 0))
    print(f"Selected viral topic: {(best.get('title') or '')[:60]}...")
    return best
