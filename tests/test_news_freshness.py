"""Recency helpers: URL date fallback, no stale unfiltered picks."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import enhanced_news_diversity as end


def test_published_date_from_cnbc_url():
    dt = end._published_date_from_url("https://www.cnbc.com/2026/03/30/foo/bar.html")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 3 and dt.day == 30


def test_article_dt_falls_back_to_url_when_no_pub_field():
    a = {
        "title": "Test",
        "url": "https://www.cnbc.com/2026/03/30/story-slug.html",
        "publishedAt": "",
    }
    dt = end._article_published_dt_utc(a)
    assert dt is not None
    assert dt.year == 2026


def test_pick_freshest_delegates_to_get_fresh(monkeypatch):
    called = {}

    def _fake():
        called["ok"] = True
        return {"title": "X"}

    monkeypatch.setattr(end, "get_fresh_viral_news", _fake)
    assert end.pick_freshest_postable_article() == {"title": "X"}
    assert called.get("ok") is True
