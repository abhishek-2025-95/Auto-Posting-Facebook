"""Tests for manual_cursor_video_flow — run: python -m pytest tests/test_manual_cursor_video_flow.py -v"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import os
import shutil
import subprocess
import sys
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from manual_cursor_video_flow import (
    IDEAL_NARRATION_MAX_SECONDS,
    IDEAL_NARRATION_MIN_SECONDS,
    MIN_VIDEO_SCENES,
    merge_research_into_narration_body,
    narration_body_from_social_caption,
    compose_video_narration_for_publish,
    _scene_duration_ratios_from_subtitle,
    _subtitle_burn_in_lines,
    build_cursor_prompt_pack,
    build_final_manual_cursor_video,
    build_manual_video_story_arc,
    build_render_plan,
    generate_five_scene_images_for_article,
    infer_visual_domain_from_story,
    load_cursor_tool_scene_paths_if_present,
    render_manual_video_from_images,
    ideal_narration_seconds_for_article,
    required_scene_count,
    write_cursor_operator_bundle,
)

_NO_IDEAL = dict(use_ideal_narration_policy=False)


def _sample_article():
    return {
        "title": "Fed holds rates steady as inflation cools",
        "summary": "Officials left the benchmark unchanged while signaling patience on cuts.",
        "url": "https://example.com/fed",
    }


def test_ideal_narration_seconds_for_article_stays_in_band():
    lo = ideal_narration_seconds_for_article({"title": "Hi", "summary": "Short."})
    hi_art = {
        "title": "Fed oil war earnings merger sanctions shutdown",
        "summary": " ".join(["Markets moved on data."] * 12),
        "research_brief": {
            "bullets": [f"Bullet {i} with enough text here for context." for i in range(12)],
        },
    }
    hi = ideal_narration_seconds_for_article(hi_art)
    assert IDEAL_NARRATION_MIN_SECONDS <= lo <= IDEAL_NARRATION_MAX_SECONDS
    assert IDEAL_NARRATION_MIN_SECONDS <= hi <= IDEAL_NARRATION_MAX_SECONDS


def test_merge_research_appends_nonredundant_bullets():
    article = {
        "title": "Headline",
        "summary": "Brief.",
        "research_brief": {
            "bullets": [
                "Distinct logistics and freight repricing followed the initial headline.",
                "Policymakers signaled monitoring of second-round price effects.",
            ],
        },
    }
    m = merge_research_into_narration_body("Headline\n\nBrief.", article)
    assert "logistics" in m.lower()
    assert "policymakers" in m.lower()


def test_narration_body_from_social_caption_strips_hashtag_tail():
    cap = (
        "First paragraph explains the story in depth for readers.\n\n"
        "Second paragraph adds detail and context.\n\n"
        "#Breaking #News #Markets #Economy"
    )
    body = narration_body_from_social_caption(cap)
    assert "#Breaking" not in body
    assert "Second paragraph" in body


def test_compose_video_narration_layers_caption_research():
    article = {
        "title": "Oil and plastics",
        "summary": "Short lede.",
        "research_brief": {"bullets": ["Refinery margins adjust with a lag to crude shocks."]},
    }
    cap = "Analysts note pass-through to consumer packaging takes several weeks.\n\n#News"
    out = compose_video_narration_for_publish(article, social_caption=cap)
    assert "Short lede" in out
    assert "Analysts note" in out
    assert "Refinery margins" in out


def test_compose_drops_caption_sentences_that_repeat_summary():
    article = {
        "title": "Oil prices surge",
        "summary": "Crude jumped after supply disruption in the Gulf region.",
        "research_brief": {"bullets": ["Refinery run cuts may follow if outages persist for several weeks."]},
    }
    cap = (
        "Crude jumped after supply disruption in the Gulf region. "
        "Inventories are being drawn down faster than traders expected.\n\n#News"
    )
    out = compose_video_narration_for_publish(article, social_caption=cap)
    assert out.lower().count("crude jumped after supply disruption") == 1
    assert "inventories" in out.lower()
    assert article.get("narration_research_already_merged") is True


def test_story_arc_skips_second_research_merge_when_flag_set():
    article = {
        "title": "T",
        "summary": "S.",
        "subtitle_text": "T\n\nS.\n\nAlready merged unique line about zebras and freight lanes.",
        "narration_research_already_merged": True,
        "research_brief": {
            "bullets": [
                "This bullet would duplicate the arc if merged again with enough distinct words here.",
            ],
        },
    }
    arc = build_manual_video_story_arc(article)
    assert "zebra" in arc["subtitle_text"].lower()
    assert "duplicate the arc" not in arc["subtitle_text"].lower()


def test_ideal_narration_policy_expands_subtitle_with_research_bullets():
    article = {
        "title": "Brief headline",
        "summary": "One sentence only.",
        "research_brief": {
            "bullets": [
                "Energy routes face renewed disruption risk and freight is repricing quickly.",
                "Downstream chemicals and packaging costs tend to lag crude but converge when shocks persist.",
            ],
        },
    }
    arc = build_manual_video_story_arc(article)
    assert arc.get("narration_expansion_enabled") is True
    assert arc["ideal_narration_seconds"] >= IDEAL_NARRATION_MIN_SECONDS
    assert len(arc["subtitle_text"]) > len("Brief headline\n\nOne sentence only.")
    assert arc["scene_count"] >= MIN_VIDEO_SCENES


def test_build_manual_video_story_arc_shape_and_timing():
    article = _sample_article()
    arc = build_manual_video_story_arc(article, **_NO_IDEAL)
    assert arc["scene_count"] == MIN_VIDEO_SCENES
    assert len(arc["scenes"]) == MIN_VIDEO_SCENES
    assert arc["duration_seconds"] == int(round(MIN_VIDEO_SCENES * 3.6))
    st = arc["subtitle_text"]
    assert isinstance(st, str)
    assert st.strip() != ""
    assert "\n\n" in st
    head, body = st.split("\n\n", 1)
    assert article["title"] in head
    assert article["summary"] in body


def test_subtitle_burn_in_lines_inserts_paragraph_gap():
    lines = _subtitle_burn_in_lines("Short headline.\n\nLonger body text that should wrap across.", max_chars=20)
    assert None in lines
    assert any("headline" in (x or "").lower() for x in lines if x)


def test_build_manual_video_story_arc_subtitle_text_override_from_article():
    article = {
        "title": "Headline only",
        "description": "Short meta description.",
        "subtitle_text": "Custom long narration for TTS.\n\nSecond block.",
    }
    arc = build_manual_video_story_arc(article, **_NO_IDEAL)
    assert arc["subtitle_text"] == "Custom long narration for TTS.\n\nSecond block."


def test_build_manual_video_story_arc_scenes_structural_coherence():
    arc = build_manual_video_story_arc(_sample_article(), **_NO_IDEAL)
    scenes = arc["scenes"]
    expected_roles = ("hook", "context", "catalyst", "reaction", "outlook")
    focus_title = _sample_article()["title"]
    for i, scene in enumerate(scenes):
        assert scene["index"] == i
        assert scene["role"] == expected_roles[i % len(expected_roles)]
        assert isinstance(scene.get("teaching_point"), str)
        assert str(scene["teaching_point"]).strip() != ""
        ps = scene["prompt_summary"]
        assert isinstance(ps, str)
        assert ps.strip() != ""
        assert focus_title in ps


def test_build_manual_video_story_arc_uses_headline_and_description_fallbacks():
    arc = build_manual_video_story_arc(
        {
            "title": "   ",
            "headline": "Rupee slips after oil prices jump",
            "summary": "   ",
            "description": "Traders price in higher import costs and inflation pressure.",
        },
        **_NO_IDEAL,
    )

    assert arc["subtitle_text"].startswith("Rupee slips after oil prices jump")
    assert "Traders price in higher import costs and inflation pressure." in arc["subtitle_text"]
    for scene in arc["scenes"]:
        assert "Rupee slips after oil prices jump" in scene["prompt_summary"]


def test_build_manual_video_story_arc_handles_minimal_article_input():
    arc = build_manual_video_story_arc({}, **_NO_IDEAL)

    assert arc["scene_count"] == MIN_VIDEO_SCENES
    assert len(arc["scenes"]) == MIN_VIDEO_SCENES
    assert arc["duration_seconds"] == int(round(MIN_VIDEO_SCENES * 3.6))
    assert arc["subtitle_text"].startswith("Market update")
    for scene in arc["scenes"]:
        assert "Market update" in scene["prompt_summary"]


def test_build_cursor_prompt_pack_matches_story_scene_count():
    story = build_manual_video_story_arc(_sample_article(), **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    assert len(prompts) == story["scene_count"] == MIN_VIDEO_SCENES


def test_build_cursor_prompt_pack_rejects_too_few_scenes():
    bad = {
        "scenes": [
            {"index": i, "role": "hook", "prompt_summary": "x", "teaching_point": "t"}
            for i in range(MIN_VIDEO_SCENES - 1)
        ]
    }
    with pytest.raises(ValueError):
        build_cursor_prompt_pack(bad)


def test_build_cursor_prompt_pack_each_has_continuity_note():
    story = build_manual_video_story_arc(_sample_article(), **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    for entry in prompts:
        assert "continuity" in entry
        assert isinstance(entry["continuity"], str)
        assert entry["continuity"].strip() != ""


def test_build_cursor_prompt_pack_continuity_ties_scenes_to_same_event_arc():
    story = build_manual_video_story_arc(_sample_article(), **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    c0 = prompts[0]["continuity"].lower()
    assert any(
        w in c0 for w in ("first", "open", "begin", "establish", "hook", "start", "initial")
    )
    for i in range(1, len(prompts)):
        c = prompts[i]["continuity"].lower()
        assert any(
            w in c
            for w in (
                "previous",
                "prior",
                "scene",
                "follow",
                "continue",
                "same",
                "sequence",
                "earlier",
            )
        ), f"scene {i} continuity should reference progression from earlier in the arc"


def test_build_cursor_prompt_pack_prompts_carry_story_focus():
    article = _sample_article()
    story = build_manual_video_story_arc(article, **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    title = article["title"]
    for entry, scene in zip(prompts, story["scenes"], strict=True):
        assert "prompt" in entry
        assert isinstance(entry["prompt"], str)
        assert title in entry["prompt"]
        assert entry["prompt"].strip() != ""
        tp = str(scene.get("teaching_point") or "")
        assert tp.strip() != ""
        assert tp in entry["prompt"]
        assert "PRIMARY FACT THIS FRAME MUST VISUALLY EXPLAIN" in entry["prompt"]


def test_build_cursor_prompt_pack_aligns_roles_with_story_scenes():
    story = build_manual_video_story_arc(_sample_article(), **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    for scene, entry in zip(story["scenes"], prompts, strict=True):
        assert entry["scene_index"] == scene["index"]
        assert entry["role"] == scene["role"]


def test_infer_visual_domain_memory_story_micron():
    story = build_manual_video_story_arc(
        {
            "title": "Micron stock slides on memory pricing worries",
            "summary": "Traders weigh DRAM spot trends and fab utilization.",
        },
        **_NO_IDEAL,
    )
    assert infer_visual_domain_from_story(story) == "memory_semiconductor"


def test_infer_visual_domain_energy_petrochemical_story():
    story = build_manual_video_story_arc(
        {
            "title": "Oil jumps on Strait of Hormuz worries; plastics costs in focus",
            "summary": "Traders weigh shipping risk and petrochemical feedstock pass-through.",
        },
        **_NO_IDEAL,
    )
    assert infer_visual_domain_from_story(story) == "energy_petrochemical"


def test_build_manual_video_story_arc_merges_research_brief_into_teaching():
    article = {
        "title": "Fed holds rates steady as inflation cools",
        "summary": "Officials left the benchmark unchanged while signaling patience on cuts.",
        "research_brief": {
            "bullets": [
                "The federal funds rate remained in the target range as policymakers cited lagged effects of prior tightening.",
                "Market-implied cut probabilities shifted after the press conference tone.",
            ],
            "sources": ["fixture"],
        },
    }
    arc = build_manual_video_story_arc(article, **_NO_IDEAL)
    assert arc.get("research_digest")
    assert "SECONDARY RESEARCH" not in arc["research_digest"]  # digest is plain facts
    assert "federal funds" in arc["research_digest"].lower()
    joined_tp = " ".join(str(s.get("teaching_point") or "") for s in arc["scenes"]).lower()
    assert "market-implied" in joined_tp or "press conference" in joined_tp


def test_build_cursor_prompt_pack_includes_research_digest_when_present():
    article = {
        "title": "Sample macro headline",
        "summary": "One sentence from the wire.",
        "research_brief": {
            "bullets": [
                "Central banks in several regions kept policy rates on hold citing sticky services inflation.",
                "Yield curves steepened modestly as terminal-rate bets were repriced.",
            ],
            "sources": ["fixture"],
        },
    }
    story = build_manual_video_story_arc(article, **_NO_IDEAL)
    prompts = build_cursor_prompt_pack(story)
    assert any("SECONDARY RESEARCH" in p["prompt"] for p in prompts)
    assert "Central banks" in prompts[0]["prompt"] or "steepened" in prompts[0]["prompt"]


def test_infer_visual_domain_general_not_dramatic_false_positive():
    story = build_manual_video_story_arc(
        {
            "title": "Fed delivers dramatic rate guidance shift",
            "summary": "Bonds repriced as officials surprised markets.",
        },
        **_NO_IDEAL,
    )
    assert infer_visual_domain_from_story(story) == "general"


def test_build_cursor_prompt_pack_memory_story_includes_specialized_beats():
    story = build_manual_video_story_arc(
        {
            "title": "Micron slides as memory glut weighs on outlook",
            "summary": "Semiconductor peers reprice on inventory fears.",
        },
        **_NO_IDEAL,
    )
    prompts = build_cursor_prompt_pack(story)
    assert all(p.get("visual_domain") == "memory_semiconductor" for p in prompts)
    p2 = next(p for p in prompts if p["role"] == "catalyst")
    assert "inventory" in p2["prompt"].lower() or "glut" in p2["prompt"].lower()
    p3 = next(p for p in prompts if p["role"] == "reaction")
    assert "peer" in p3["prompt"].lower() or "s&p" in p3["prompt"].lower()
    p4 = next(p for p in prompts if p["role"] == "outlook")
    assert "earnings" in p4["prompt"].lower() or "guidance" in p4["prompt"].lower()
    assert "dimm" in prompts[0]["prompt"].lower() or "dram" in prompts[0]["prompt"].lower()


def test_scene_duration_ratios_headline_plus_body_splits_into_five():
    body = " ".join([f"Sentence {i} ends here. " for i in range(12)])
    sub = f"Headline line.\n\n{body}"
    r = _scene_duration_ratios_from_subtitle(sub, 5)
    assert r is not None and len(r) == 5
    assert abs(sum(r) - 1.0) < 1e-5
    assert all(x > 0 for x in r)


def test_scene_duration_ratios_headline_plus_body_splits_into_ten():
    body = " ".join([f"Sentence {i} ends here. " for i in range(24)])
    sub = f"Headline line.\n\n{body}"
    r = _scene_duration_ratios_from_subtitle(sub, 10)
    assert r is not None and len(r) == 10
    assert abs(sum(r) - 1.0) < 1e-5
    assert all(x > 0 for x in r)


def test_required_scene_count_audio_and_minimum():
    assert required_scene_count(audio_seconds=15.0) == MIN_VIDEO_SCENES
    assert required_scene_count(audio_seconds=100.0) == 10
    assert required_scene_count(audio_seconds=101.0) == 11


def test_render_manual_video_from_images_requires_at_least_one_image():
    with pytest.raises(ValueError, match="at least one"):
        render_manual_video_from_images([], output_path=os.path.join(_ROOT, "out.mp4"))


def test_render_manual_video_from_images_returns_none_when_image_missing(tmp_path):
    png = _minimal_png_bytes()
    paths = []
    for i in range(5):
        p = tmp_path / f"{i}.png"
        if i != 2:
            p.write_bytes(png)
        paths.append(str(p))
    out = tmp_path / "out.mp4"
    assert render_manual_video_from_images(paths, output_path=str(out)) is None


def test_render_manual_video_from_images_mocked_concat(tmp_path, monkeypatch):
    """No real ffmpeg: fake per-scene clips and concat subprocess."""
    png = _minimal_png_bytes()
    image_paths = []
    for i in range(10):
        p = tmp_path / f"{i}.png"
        p.write_bytes(png)
        image_paths.append(str(p))

    clip_calls = []

    def fake_clip(image_path, output_path=None, duration_seconds=6, width=720, height=900, effect="zoom", fps=30):
        clip_calls.append((image_path, duration_seconds))
        assert output_path is not None
        with open(output_path, "wb") as f:
            f.write(b"fake-mp4")
        return output_path

    def fake_run(cmd, **kwargs):
        if cmd[:4] == ["ffmpeg", "-y", "-f", "concat"] or (
            len(cmd) >= 2 and cmd[0] == "ffmpeg" and "-f" in cmd and "concat" in cmd
        ):
            out = cmd[-1]
            with open(out, "wb") as f:
                f.write(b"joined")
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        raise AssertionError(f"unexpected subprocess: {cmd}")

    monkeypatch.setattr("manual_cursor_video_flow.image_to_video_clip", fake_clip)
    monkeypatch.setattr("manual_cursor_video_flow.subprocess.run", fake_run)

    out = tmp_path / "manual.mp4"
    result = render_manual_video_from_images(image_paths, output_path=str(out))
    assert result == str(out.resolve())
    assert out.is_file()
    assert len(clip_calls) == 10
    for _, dur in clip_calls:
        assert abs(dur - 3.6) < 0.01


def _minimal_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmWQQAAAABJRU5ErkJggg=="
    )


def test_build_render_plan_includes_branding_and_full_summary_mode():
    plan = build_render_plan(_sample_article(), use_ideal_narration_policy=False)
    assert plan["subtitles_mode"] == "full_summary"
    b = plan["branding"]
    assert b["breaking_news"] is True
    assert b["ai_generated"] is True
    assert b["unseen_economy_logo"] is True
    assert plan["story_pack"]["scene_count"] == MIN_VIDEO_SCENES


def test_build_final_manual_cursor_video_stitch_only(tmp_path):
    png = _minimal_png_bytes()
    paths = []
    for i in range(5):
        p = tmp_path / f"{i}.png"
        p.write_bytes(png)
        paths.append(str(p))

    out = tmp_path / "only.mp4"
    result = build_final_manual_cursor_video(
        paths,
        output_path=str(out),
        subtitle_text="ignored",
        subtitles=False,
        branding=False,
        fps=24,
    )
    assert result is not None
    assert out.is_file()


def test_build_final_premium_rejects_insufficient_scenes_for_audio(tmp_path, monkeypatch):
    png = _minimal_png_bytes()
    paths = []
    for i in range(5):
        p = tmp_path / f"{i}.png"
        p.write_bytes(png)
        paths.append(str(p))

    def fake_synth(text, out_wav, **kwargs):
        with open(out_wav, "wb") as f:
            f.write(b"x")
        return out_wav

    monkeypatch.setattr("premium_voice_subtitles.synthesize_kokoro_wav", fake_synth)
    monkeypatch.setattr("premium_voice_subtitles._ffprobe_duration_seconds", lambda path: 120.0)

    out = tmp_path / "prem.mp4"
    r = build_final_manual_cursor_video(
        paths,
        output_path=str(out),
        subtitle_text="Fed holds rates steady while markets digest guidance and forward path.",
        subtitles=False,
        branding=False,
        premium_voice_subtitles=True,
        pycaps_kinetic_subtitles=False,
    )
    assert r is None


def test_build_final_manual_cursor_video_mocked_pipeline(tmp_path, monkeypatch):
    png = _minimal_png_bytes()
    paths = []
    for i in range(5):
        p = tmp_path / f"{i}.png"
        p.write_bytes(png)
        paths.append(str(p))

    def fake_stitch(image_paths, output_path, **kw):
        with open(output_path, "wb") as f:
            f.write(b"stitched")
        return os.path.abspath(output_path)

    def fake_sub(video_path, subtitle_text, output_path):
        assert "hello" in subtitle_text
        with open(output_path, "wb") as f:
            f.write(b"subbed")
        return os.path.abspath(output_path)

    def fake_brand(video_path, headline=None, output_path=None, **kwargs):
        assert output_path is not None
        with open(output_path, "wb") as f:
            f.write(b"final")
        return os.path.abspath(output_path)

    monkeypatch.setattr("manual_cursor_video_flow.render_manual_video_from_images", fake_stitch)
    monkeypatch.setattr("manual_cursor_video_flow.apply_full_summary_subtitles_to_video", fake_sub)
    monkeypatch.setattr("video_branding.brand_video_for_posting", fake_brand)

    out = tmp_path / "final.mp4"
    r = build_final_manual_cursor_video(
        paths,
        output_path=str(out),
        subtitle_text="hello world summary",
        headline="H1",
    )
    assert r == str(out.resolve())
    assert out.read_bytes() == b"final"


def _load_render_manual_cursor_cli():
    path = os.path.join(_ROOT, "scripts", "render_manual_cursor_video.py")
    spec = importlib.util.spec_from_file_location("_render_manual_cursor_video_cli", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_generate_five_scene_images_always_cursor_only_stub(tmp_path):
    article = _sample_article()
    assert generate_five_scene_images_for_article(article, str(tmp_path)) is None


def test_write_cursor_operator_bundle_and_load_scenes(tmp_path):
    article = _sample_article()
    aj = tmp_path / "article.json"
    aj.write_text(__import__("json").dumps(article), encoding="utf-8")
    pack, paste, readme, story, prompts = write_cursor_operator_bundle(
        str(tmp_path), article, use_ideal_narration_policy=False
    )
    assert os.path.isfile(pack) and os.path.isfile(paste) and os.path.isfile(readme)
    assert len(prompts) == story["scene_count"] == MIN_VIDEO_SCENES
    assert load_cursor_tool_scene_paths_if_present(str(tmp_path), MIN_VIDEO_SCENES) is None
    png = _minimal_png_bytes()
    for i in range(MIN_VIDEO_SCENES):
        (tmp_path / f"scene{i}.png").write_bytes(png)
    loaded = load_cursor_tool_scene_paths_if_present(str(tmp_path), MIN_VIDEO_SCENES)
    assert loaded is not None and len(loaded) == MIN_VIDEO_SCENES


def test_fetch_us_uk_pack_writes_pack_without_news_network(tmp_path, monkeypatch):
    def _fake():
        return {
            "title": "BoE holds benchmark rate steady (US)",
            "description": "Sterling drifted as traders weighed inflation data.",
            "url": "https://example.com/story",
            "source": "Reuters (GB)",
        }

    monkeypatch.setattr("enhanced_news_diversity.get_fresh_viral_news_us_uk", _fake)
    mod = _load_render_manual_cursor_cli()
    out = tmp_path / "cursor_batch"
    code = mod.cmd_fetch_us_uk_pack(
        argparse.Namespace(out_dir=str(out), research=False, ideal_narration_policy=False)
    )
    assert code == 0
    pack = out / "cursor_video_pack.json"
    art = out / "article.json"
    assert pack.is_file() and art.is_file()
    data = __import__("json").loads(pack.read_text(encoding="utf-8"))
    assert data.get("images_policy") == "cursor_image_tool_only"
    assert len(data.get("cursor_prompts") or []) == MIN_VIDEO_SCENES
    assert "BoE holds" in data["article"]["title"]
    paste = out / "CURSOR_IMAGE_PROMPTS_PASTE.txt"
    assert paste.is_file()
    assert "SCENE 0" in paste.read_text(encoding="utf-8")


def test_cli_prompts_writes_json(tmp_path):
    import subprocess

    article = {
        "title": "CLI test headline",
        "summary": "CLI test summary body.",
    }
    aj = tmp_path / "article.json"
    aj.write_text(__import__("json").dumps(article), encoding="utf-8")
    out = tmp_path / "pack.json"
    proc = subprocess.run(
        [
            sys.executable,
            os.path.join(_ROOT, "scripts", "render_manual_cursor_video.py"),
            "prompts",
            "--no-ideal-narration-policy",
            "--article",
            str(aj),
            "-o",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    data = __import__("json").loads(out.read_text(encoding="utf-8"))
    assert len(data["cursor_prompts"]) == MIN_VIDEO_SCENES
    assert data["story_pack"]["duration_seconds"] == int(round(MIN_VIDEO_SCENES * 3.6))
    assert "CLI test headline" in data["story_pack"]["subtitle_text"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not on PATH")
def test_render_manual_video_from_images_integration_duration(tmp_path):
    png = _minimal_png_bytes()
    paths = []
    for i in range(5):
        p = tmp_path / f"{i}.png"
        p.write_bytes(png)
        paths.append(str(p))
    out = tmp_path / "story.mp4"
    result = render_manual_video_from_images(paths, output_path=str(out), fps=24)
    assert result is not None
    assert os.path.isfile(result)
    pr = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    duration = float(pr.stdout.strip())
    assert 17.5 <= duration <= 18.5
