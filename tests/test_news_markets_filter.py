"""Sanity check for US/EU markets article filter. Run: python tests/test_news_markets_filter.py"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from news_fetcher import article_matches_markets_us_europe as match  # noqa: E402


def main() -> int:
    assert match(
        {
            "title": "Fed holds rates as Wall Street eyes inflation data",
            "description": "US stocks and Treasury yields move.",
            "source": "Reuters (US)",
            "url": "https://example.com/a",
        }
    )
    assert not match(
        {
            "title": "Super Bowl halftime lineup revealed",
            "description": "NFL season preview",
            "source": "ESPN",
            "url": "https://example.com/b",
        }
    )
    print("test_news_markets_filter: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
