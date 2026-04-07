"""Tests for breaking headline + reputed source helpers. Run: python tests/test_breaking_reputed_filter.py"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from news_fetcher import (  # noqa: E402
    _headline_is_breaking_finance,
    _source_is_reputed_finance_outlet,
)


def main() -> int:
    assert _source_is_reputed_finance_outlet("Reuters (US)")
    assert _source_is_reputed_finance_outlet("BBC Business")
    assert not _source_is_reputed_finance_outlet("Reddit r/stocks")
    assert not _source_is_reputed_finance_outlet("Google News")

    assert _headline_is_breaking_finance("BREAKING: Stocks plunge after Fed decision", "")
    assert _headline_is_breaking_finance(
        "S&P 500 futures surge as traders eye ECB meeting", ""
    )
    assert not _headline_is_breaking_finance(
        "Quiet day expected on Wall Street ahead of holiday", ""
    )
    # Calmer macro + markets/economy context (still on-brief)
    assert _headline_is_breaking_finance(
        "UK GDP growth slows; investors watch stock market reaction", ""
    )

    print("test_breaking_reputed_filter: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
