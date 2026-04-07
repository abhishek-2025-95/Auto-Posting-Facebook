"""Tests for news_evidence_text optional extract + sanitize helpers."""
from __future__ import annotations

from manual_cursor_video_flow import build_manual_video_story_arc
from news_evidence_text import (
    extract_numeric_chips,
    extract_stat_sentences,
    sanitize_subtitle_numbers,
)


def test_extract_stat_sentences_finds_digit_sentences():
    title = "Markets fall"
    body = "The S&P 500 lost 1.2%. Oil rose above $82. No third sentence."
    s = extract_stat_sentences(title, body)
    assert len(s) >= 2
    assert any("1.2" in x for x in s)
    assert any("82" in x for x in s)


def test_extract_numeric_chips_dollar_and_percent():
    t = "Revenue hit $3.1 billion while margins slid 40 bps to 12.4%."
    chips = extract_numeric_chips(t)
    assert any("$" in c for c in chips)
    assert any("%" in c for c in chips)


def test_story_arc_subtitle_is_plain_title_and_summary_no_by_numbers_block():
    article = {
        "title": "Co X warns on outlook",
        "summary": "Shares fell 5% after the firm cut Q2 guidance by $200M.",
    }
    arc = build_manual_video_story_arc(article, use_ideal_narration_policy=False)
    sub = arc["subtitle_text"]
    assert "By the numbers" not in sub
    assert article["title"] in sub
    assert article["summary"] in sub


def test_sanitize_strips_numbers_absent_from_news():
    article = {
        "title": "Fed holds rates",
        "summary": "Officials left the benchmark at 5.25 to 5.5 percent.",
    }
    dirty = (
        "Fed holds rates\n\n"
        "Officials left the benchmark at 5.25 to 5.5 percent.\n\n"
        "By the numbers (from the reporting):\n"
        "• Revenue was $999.9B surprise\n"
        "• Margins 5.25%"
    )
    clean = sanitize_subtitle_numbers(dirty, article)
    assert "999" not in clean
    assert "$999" not in clean
