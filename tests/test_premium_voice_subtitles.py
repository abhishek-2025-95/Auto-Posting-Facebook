"""Unit tests for premium_voice_subtitles helpers."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from premium_voice_subtitles import (
    _atempo_filter_chain,
    _ffprobe_duration_seconds,
    extend_or_trim_video_duration_ffmpeg,
    narration_text_for_tts,
    whisper_raw_result_to_pycaps_whisper_json,
)


def test_narration_text_for_tts_inserts_pause_token_between_paragraphs():
    s = "Headline here.\n\nSecond paragraph body."
    out = narration_text_for_tts(s)
    assert "...s" in out
    assert "\n" not in out
    assert "Headline" in out
    assert "Second paragraph" in out


def test_narration_text_for_tts_collapses_whitespace():
    assert narration_text_for_tts("a  \n  b") == "a b"


def test_atempo_chain_splits_large_factors():
    chain = _atempo_filter_chain(3.5)
    assert "atempo=2.0" in chain
    assert "atempo=" in chain


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not on PATH")
def test_extend_or_trim_video_duration_extends_and_trims(tmp_path):
    src = tmp_path / "base.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:d=2",
            "-pix_fmt",
            "yuv420p",
            str(src),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    longer = tmp_path / "long.mp4"
    assert extend_or_trim_video_duration_ffmpeg(str(src), str(longer), 3.25)
    d_long = _ffprobe_duration_seconds(str(longer))
    assert d_long is not None and 3.05 <= d_long <= 3.45

    shorter = tmp_path / "short.mp4"
    assert extend_or_trim_video_duration_ffmpeg(str(src), str(shorter), 1.0)
    d_short = _ffprobe_duration_seconds(str(shorter))
    assert d_short is not None and 0.85 <= d_short <= 1.15


def test_whisper_raw_to_pycaps_json_fills_pseudo_words_when_missing():
    data = {
        "language": "en",
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "text": "alpha beta", "words": []},
        ],
    }
    out = whisper_raw_result_to_pycaps_whisper_json(data)
    assert out["language"] == "en"
    assert len(out["segments"]) == 1
    w = out["segments"][0]["words"]
    assert len(w) == 2
    assert w[0]["word"] == "alpha"
    assert w[1]["word"] == "beta"
    assert w[0]["start"] < w[0]["end"] <= w[1]["end"]
