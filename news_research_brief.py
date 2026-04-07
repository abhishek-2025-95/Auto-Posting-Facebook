"""
Lightweight secondary research for news-driven explainer stills.

Fetches a short Wikipedia lead (via search + REST summary) and a few DuckDuckGo HTML
snippets to widen teaching points and image prompts beyond the RSS blurb.

Network failures return an empty brief; the pipeline still runs on title + summary only.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _DEFAULT_UA, "Accept-Language": "en-US,en;q=0.9"})
    return s


def _dedupe_bullets(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in items:
        t = " ".join(x.split()).strip()
        if len(t) < 28:
            continue
        key = t.lower()[:96]
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def _wiki_summary_for_query(session: requests.Session, q: str, *, timeout: float) -> Optional[str]:
    q = (q or "").strip()
    if len(q) < 4:
        return None
    try:
        r = session.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": q[:280],
                "srlimit": 1,
                "format": "json",
            },
            timeout=timeout,
        )
        r.raise_for_status()
        hits = (r.json().get("query") or {}).get("search") or []
        if not hits:
            return None
        title = hits[0].get("title") or ""
        if not title:
            return None
        path = quote(title.replace(" ", "_"), safe="(),'%")
        r2 = session.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{path}",
            timeout=timeout,
        )
        if r2.status_code != 200:
            return None
        data = r2.json()
        return (data.get("extract") or "").strip() or None
    except (OSError, requests.RequestException, ValueError, KeyError):
        return None


def _wiki_bullets(text: str, *, max_sentences: int = 5, max_len: int = 320) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out: List[str] = []
    for p in parts:
        s = p.strip()
        if len(s) < 35:
            continue
        out.append(s[:max_len])
        if len(out) >= max_sentences:
            break
    return out


def _ddg_snippets(
    session: requests.Session,
    query: str,
    *,
    timeout: float,
    max_n: int = 5,
) -> List[str]:
    q = (query or "").strip()
    if len(q) < 4:
        return []
    try:
        r = session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": q[:300]},
            timeout=timeout,
        )
        r.raise_for_status()
    except (OSError, requests.RequestException):
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    raw: List[str] = []
    for sel in ("a.result__snippet", "td.result-snippet"):
        for el in soup.select(sel):
            t = el.get_text(" ", strip=True)
            if len(t) > 45:
                raw.append(t[:420])
            if len(raw) >= max_n * 2:
                break
        if len(raw) >= max_n:
            break
    return raw[:max_n]


def gather_secondary_research(
    article: Mapping[str, Any],
    *,
    timeout: float = 12.0,
    max_bullets: int = 14,
) -> Dict[str, Any]:
    title = str(article.get("title") or article.get("headline") or "").strip()
    summary = str(article.get("summary") or article.get("description") or "").strip()
    if not title and not summary:
        return {"bullets": [], "sources": [], "queries": []}

    wiki_q = title[:200] if title else summary[:200]
    queries: List[str] = []
    if title:
        queries.append(title[:200])
        queries.append(f"{title[:100]} market impact explained")
    if summary and summary not in queries:
        queries.append((summary[:140] + " context").strip())

    bullets: List[str] = []
    sources: List[str] = []
    session = _session()

    wiki_text = _wiki_summary_for_query(session, wiki_q, timeout=timeout)
    if wiki_text:
        bullets.extend(_wiki_bullets(wiki_text))
        sources.append("wikipedia")

    for q in queries[:3]:
        try:
            sn = _ddg_snippets(session, q, timeout=timeout, max_n=4)
            if sn:
                bullets.extend(sn)
                if "duckduckgo" not in sources:
                    sources.append("duckduckgo")
        except Exception:
            pass

    bullets = _dedupe_bullets(bullets)[:max_bullets]
    return {
        "bullets": bullets,
        "sources": list(dict.fromkeys(sources)),
        "queries": queries[:3],
    }


def research_digest(brief: Mapping[str, Any], *, max_chars: int = 950) -> str:
    bullets = brief.get("bullets") or []
    if not isinstance(bullets, list) or not bullets:
        return ""
    parts = [str(b).strip() for b in bullets if str(b).strip()]
    joined = " | ".join(parts)
    if len(joined) <= max_chars:
        return joined
    return joined[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def enrich_article_with_research(
    article: Mapping[str, Any],
    *,
    timeout: float = 12.0,
    max_bullets: int = 14,
) -> Dict[str, Any]:
    """Return a copy of ``article`` with ``research_brief`` filled from web sources."""
    out = dict(article)
    out["research_brief"] = gather_secondary_research(
        out, timeout=timeout, max_bullets=max_bullets
    )
    return out
