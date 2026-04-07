"""
Manual assisted video story pack: one finance-news article -> multi-scene explainer arc.
Default: at least 10 scenes and enough scenes to cover narration at ≥1 image per 10 seconds (see ``required_scene_count``).
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from typing import Any, Dict, List, Mapping, Optional, Sequence

from image_to_video_clip import image_to_video_clip
from news_research_brief import research_digest

try:
    from config import AUTO_EXPAND_VIDEO_NARRATION as _AUTO_EXPAND_VIDEO_NARRATION
except ImportError:
    _AUTO_EXPAND_VIDEO_NARRATION = True

# Explainer videos: minimum scene count and ≥1 image per this many seconds of narration (see ``required_scene_count``).
MIN_VIDEO_SCENES = 10
AUDIO_SECONDS_PER_SCENE = 10.0

# Planning: ~132 wpm comfortable VO; used with ``ideal_narration_seconds_for_article`` expansion targets.
NARRATION_WORDS_PER_SECOND_PLANNING = 2.2
IDEAL_NARRATION_MIN_SECONDS = 55.0
IDEAL_NARRATION_MAX_SECONDS = 165.0

_GENERIC_EXPLAINER_BRIDGES: tuple[str, ...] = (
    "Markets are repricing how this flows through commodities, downstream prices, and corporate margins.",
    "Investors are weighing second-round effects on inflation expectations and what central banks might do next.",
    "The read-through for portfolios is volatility in risk assets until the channel and duration of the shock are clearer.",
    "Watch spreads, freight and inventory data, and whether policymakers signal containment or escalation.",
    "Until the next hard data print, positioning will stay sensitive to headlines and liquidity conditions.",
)


def _narration_word_count(subtitle_text: str) -> int:
    flat = (subtitle_text or "").replace("\n\n", " ").strip()
    if not flat:
        return 0
    return len(re.sub(r"\s+", " ", flat).split())


def ideal_narration_seconds_for_article(article: Mapping[str, Any]) -> float:
    """
    Heuristic target length (seconds) for a full explainer with comfortable VO — not measured audio.
    Uses headline, summary, optional ``research_brief`` bullets, and simple complexity signals.
    """
    title = _first_non_blank(article.get("title"), article.get("headline"), default="")
    extra = _first_non_blank(article.get("summary"), article.get("description"), default="")
    blob = f"{title} {extra}".strip().lower()
    words = max(0, len(blob.split()))

    rb = article.get("research_brief") if isinstance(article.get("research_brief"), dict) else {}
    bullets = rb.get("bullets") if isinstance(rb.get("bullets"), list) else []
    n_bullets = len([b for b in bullets if str(b).strip()])

    comp = 0.0
    if _TRIGGER_HINT_RE.search(blob):
        comp += 1.0
    if _REACTION_HINT_RE.search(blob):
        comp += 1.0
    sentences = len(_summary_sentences(extra))
    if sentences >= 4:
        comp += 1.0
    if sentences >= 7:
        comp += 1.0
    if n_bullets >= 8:
        comp += 1.5
    elif n_bullets >= 4:
        comp += 1.0
    elif n_bullets >= 1:
        comp += 0.5

    # Short wire -> ~1 min; rich context + complexity -> up to ~2.5 min cap
    sec = 66.0 + min(36.0, words * 0.42) + comp * 12.5 + min(30.0, n_bullets * 3.2)
    return max(IDEAL_NARRATION_MIN_SECONDS, min(IDEAL_NARRATION_MAX_SECONDS, sec))


def _bullet_normalized_for_dedupe(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _significant_words(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{4,}", (s or "").lower()))


def _word_overlap_ratio(words: set[str], haystack_lower: str) -> float:
    if not words:
        return 0.0
    hw = set(re.findall(r"[a-z0-9]{4,}", haystack_lower))
    if not hw:
        return 0.0
    return len(words & hw) / len(words)


def _sentence_redundant_with_corpus(sentence: str, corpus_lower: str) -> bool:
    """True when most significant terms in *sentence* already appear in *corpus_lower*."""
    s = (sentence or "").strip()
    if len(s) < 18:
        return False
    sw = _significant_words(s)
    if len(sw) < 3:
        return False
    return _word_overlap_ratio(sw, corpus_lower) >= 0.58


def _filter_redundant_caption_block(base: str, caption_block: str) -> str:
    """Drop caption sentences that largely repeat the headline/summary lede."""
    cap = (caption_block or "").strip()
    if not cap:
        return ""
    corpus = (base or "").lower()
    raw = re.sub(r"\s*\n\s*", " ", cap)
    parts = _SENTENCE_SPLIT_RE.split(raw)
    kept: List[str] = []
    for p in parts:
        seg = p.strip()
        if len(seg) < 12:
            continue
        if _sentence_redundant_with_corpus(seg, corpus):
            continue
        kept.append(seg)
    return "\n\n".join(kept).strip()


def _bridge_is_redundant(bridge: str, haystack_lower: str) -> bool:
    b = (bridge or "").strip()
    if len(b) < 30:
        return False
    sw = _significant_words(b)
    if len(sw) < 4:
        return False
    return _word_overlap_ratio(sw, haystack_lower) >= 0.48


def _research_bullet_is_redundant(chunk: str, haystack_lower: str) -> bool:
    """True if this bullet repeats what is already in the narration."""
    norm = _bullet_normalized_for_dedupe(chunk)
    if len(norm) < 22:
        return True
    take = min(80, len(norm))
    if norm[:take] in haystack_lower:
        return True
    win = 36
    step = 6
    if len(norm) >= win:
        for i in range(0, len(norm) - win + 1, step):
            if norm[i : i + win] in haystack_lower:
                return True
    words = set(re.findall(r"[a-z0-9]{4,}", norm))
    if len(words) < 4:
        return False
    hw = set(re.findall(r"[a-z0-9]{4,}", haystack_lower))
    if not words:
        return False
    overlap = len(words & hw) / len(words)
    return overlap > 0.58


def _format_research_sentence(b: str, *, max_len: int = 420) -> str:
    chunk = (b or "").strip()[:max_len].rstrip()
    if not chunk:
        return ""
    if chunk[-1] not in ".!?":
        chunk += "."
    return chunk


def merge_research_into_narration_body(base: str, article: Mapping[str, Any]) -> str:
    """
    Append every ``research_brief`` bullet that is not already covered by the headline/summary/caption text.
    This is the main fix for VO that stopped at a short lede and never read secondary research.
    """
    parts: List[str] = []
    b0 = (base or "").strip()
    if b0:
        parts.append(b0)
    hay = b0.lower()
    rb = article.get("research_brief") if isinstance(article.get("research_brief"), dict) else {}
    raw_bullets = [str(x).strip() for x in (rb.get("bullets") or []) if str(x).strip()]
    for b in raw_bullets:
        chunk = _format_research_sentence(b)
        if not chunk or _research_bullet_is_redundant(chunk, hay):
            continue
        parts.append(chunk)
        hay = "\n\n".join(parts).lower()
    return "\n\n".join(p for p in parts if p.strip())


def pad_narration_with_bridges(combined: str, ideal_seconds: float) -> str:
    """Pad with neutral explainer lines until approximate word count reaches the ideal target."""
    target_words = max(
        96,
        min(680, int(float(ideal_seconds) * NARRATION_WORDS_PER_SECOND_PLANNING)),
    )
    parts: List[str] = [combined] if (combined or "").strip() else []
    wc = _narration_word_count("\n\n".join(parts))
    bi = 0
    while wc < target_words * 0.88 and bi < len(_GENERIC_EXPLAINER_BRIDGES):
        hay = "\n\n".join(parts).lower()
        bridge = _GENERIC_EXPLAINER_BRIDGES[bi]
        bi += 1
        if _bridge_is_redundant(bridge, hay):
            continue
        parts.append(bridge)
        wc = _narration_word_count("\n\n".join(parts))
    return "\n\n".join(p for p in parts if p.strip())


def narration_body_from_social_caption(caption: str, *, max_chars: int = 4500) -> str:
    """
    Strip hashtag blocks and heavy promo lines from a Facebook-style caption; keep the factual/explainer body.
    """
    if not (caption or "").strip():
        return ""
    out_lines: List[str] = []
    for line in caption.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^#(\w+)$", s):
            break
        hc = len(re.findall(r"#\w+", s))
        tokens = max(1, len(s.split()))
        if hc >= 4 and hc >= int(tokens * 0.45):
            break
        out_lines.append(s)
    text = " ".join(out_lines)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return text


def compose_video_narration_for_publish(
    article: Mapping[str, Any],
    *,
    social_caption: Optional[str] = None,
    caption_max_chars: int = 4500,
) -> str:
    """
    Full VO script for auto-posting: lede (title + summary), optional long caption body, research bullets,
    then optional bridge padding toward ideal length.
    """
    title = _first_non_blank(article.get("title"), article.get("headline"), default="")
    extra = _first_non_blank(article.get("summary"), article.get("description"), default="")
    if title and extra:
        base = f"{title}\n\n{extra}".strip()
    elif title:
        base = title
    elif extra:
        base = extra
    else:
        base = "Market update"
    if social_caption:
        cap = narration_body_from_social_caption(social_caption, max_chars=caption_max_chars)
        cap = _filter_redundant_caption_block(base, cap)
        if len(cap) > 40:
            base = f"{base}\n\n{cap}".strip()
    ideal = ideal_narration_seconds_for_article(article)
    merged = merge_research_into_narration_body(base, article)
    if _AUTO_EXPAND_VIDEO_NARRATION:
        out = pad_narration_with_bridges(merged, ideal)
    else:
        out = merged
    if isinstance(article, dict):
        article["narration_research_already_merged"] = True
    return out


def enrich_subtitle_text_for_ideal_explainer(
    article: Mapping[str, Any],
    subtitle_text: str,
    ideal_seconds: float,
) -> str:
    """Backward-compatible name: merge research, then pad toward ideal word count."""
    return pad_narration_with_bridges(
        merge_research_into_narration_body(subtitle_text, article),
        ideal_seconds,
    )


def required_scene_count(
    *,
    audio_seconds: Optional[float] = None,
    subtitle_text: Optional[str] = None,
) -> int:
    """
    At least ``MIN_VIDEO_SCENES`` images, and at least one image per ``AUDIO_SECONDS_PER_SCENE`` seconds
    of measured (or estimated) narration.
    """
    if audio_seconds is not None and float(audio_seconds) > 0:
        return max(
            MIN_VIDEO_SCENES,
            int(math.ceil(float(audio_seconds) / AUDIO_SECONDS_PER_SCENE)),
        )
    text = (subtitle_text or "").strip()
    if not text:
        return MIN_VIDEO_SCENES
    flat = text.replace("\n\n", "... ")
    words = max(1, len(flat.split()))
    est_sec = max(10.0, words / 2.35)
    return max(MIN_VIDEO_SCENES, int(math.ceil(est_sec / AUDIO_SECONDS_PER_SCENE)))


def _n_teaching_points(title: str, body: str, n: int) -> List[str]:
    n = max(MIN_VIDEO_SCENES, int(n))
    t = (title or "").strip() or "Market update"
    b = (body or "").strip()
    if n <= 1:
        return [t]
    if not b:
        return [t] + [f"{t} — angle {i}." for i in range(1, n)]
    segs = _summary_sentences(b)
    if not segs:
        return [t] + [f"{t} — angle {i}." for i in range(1, n)]
    if len(segs) >= n:
        out = [t]
        denom = max(1, n - 1)
        for k in range(1, n):
            idx = min(len(segs) - 1, int(round((k / denom) * (len(segs) - 1))))
            out.append(segs[idx])
        return out
    if n <= 5:
        base = _five_teaching_points(t, b)
        while len(base) < n:
            base.append(base[-1])
        return base[:n]
    base = _five_teaching_points(t, b)
    out = [base[i % len(base)] for i in range(n)]
    out[0] = t
    out[-1] = segs[-1]
    return out


def _role_specs_cycle() -> List[tuple[str, str]]:
    return [
        ("hook", "Lead with the headline and why it matters for finance viewers right now."),
        ("context", "Set the entities and backdrop: firms, regulators, instruments, or region."),
        ("catalyst", "Isolate the concrete trigger: data print, policy decision, filing, or guidance."),
        ("reaction", "Describe how prices, spreads, or consensus shifted on the news."),
        ("outlook", "End with the next catalyst, risk, or level to watch for this thread."),
    ]


def _first_non_blank(*values: Any, default: str = "") -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return default


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_OUTLOOK_FALLBACK = (
    "Forward: traders watch the next data prints, policy guidance, and whether risk appetite stabilizes or keeps "
    "de-risking across assets."
)
_TRIGGER_HINT_RE = re.compile(
    r"\b(oil|crude|energy|geopolitical|iran|strait|fed|ecb|boe|rate\s+hike|cut|treasury|auction|"
    r"gdp|cpi|ppi|inflation|deficit|inventory|glut|supply|earnings|guidance|default|deal|merger|sanction|"
    r"shutdown|strike|war|conflict)\b",
    re.IGNORECASE,
)
_REACTION_HINT_RE = re.compile(
    r"\b(equity|equities|stock|index|nasdaq|s&p|dow|market|bond|yield|curve|spread|reprice|volatility|vix|"
    r"fell|rose|slide|surge|rally|rout|sell[- ]?off|risk[- ]?off|safe[- ]?haven|dollar|fx|rupee|euro)\b",
    re.IGNORECASE,
)


def _summary_sentences(body: str) -> List[str]:
    """Split article body into clean sentences for per-scene teaching points."""
    raw = " ".join((body or "").split())
    if not raw:
        return []
    parts = _SENTENCE_SPLIT_RE.split(raw)
    out: List[str] = []
    for p in parts:
        s = p.strip()
        if len(s) > 12:
            out.append(s)
    return out


def _five_teaching_points(title: str, body: str) -> List[str]:
    """
    One concrete informational string per scene (hook..outlook), derived from title + summary.
    Drives image prompts so each frame explains a slice of the story, not generic mood art.
    """
    t = (title or "").strip() or "Market update"
    segs = _summary_sentences(body)
    if not segs:
        return [t, t, t, t, _OUTLOOK_FALLBACK]

    if len(segs) == 1:
        only = segs[0]
        if _TRIGGER_HINT_RE.search(only) and _REACTION_HINT_RE.search(only):
            return [t, only, t, only, _OUTLOOK_FALLBACK]
        return [t, only, only, only, _OUTLOOK_FALLBACK]

    trig = next((s for s in segs if _TRIGGER_HINT_RE.search(s)), None)
    react = next((s for s in segs if _REACTION_HINT_RE.search(s)), None)
    if trig is react and trig is not None and len(segs) > 1:
        react = next((s for s in segs if s is not trig), segs[0])

    p0 = t
    p1 = segs[0]
    p2 = trig or (segs[1] if len(segs) > 1 else t)
    p3 = react or (segs[2] if len(segs) > 2 else (segs[1] if len(segs) > 1 else segs[0]))
    if p3.strip() == p2.strip() and len(segs) > 1:
        p3 = segs[-1] if segs[-1].strip() != p2.strip() else segs[0]

    p4 = segs[-1]
    if p4.strip() == p3.strip() and len(segs) > 1:
        p4 = _OUTLOOK_FALLBACK

    return [p0, p1, p2, p3, p4]


def build_manual_video_story_arc(
    article: Mapping[str, Any],
    *,
    scene_count: Optional[int] = None,
    audio_seconds: Optional[float] = None,
    use_ideal_narration_policy: bool = True,
) -> Dict[str, Any]:
    """
    Build a story pack for a single article (dict-like: title, summary, etc.).

    When ``use_ideal_narration_policy`` is True (default), picks a per-story **ideal narration length**
    (``ideal_narration_seconds``) from headline, summary, and research bullets, optionally expands
    ``subtitle_text`` toward that target (``AUTO_EXPAND_VIDEO_NARRATION`` in config), and sizes scene
    count from expanded narration or from ideal seconds.

    Pass ``use_ideal_narration_policy=False`` for deterministic tests or legacy min-scene-only behavior.
    """
    title = _first_non_blank(article.get("title"), article.get("headline"), default="Market update")
    extra = _first_non_blank(article.get("summary"), article.get("description"))

    rb_raw = article.get("research_brief")
    rb: Dict[str, Any] = dict(rb_raw) if isinstance(rb_raw, dict) else {}
    bullets = rb.get("bullets") if isinstance(rb.get("bullets"), list) else []
    body_for_teaching = extra
    if bullets:
        blob = " ".join(str(b).strip() for b in bullets if str(b).strip())
        if blob:
            body_for_teaching = f"{extra}\n\n{blob}".strip() if extra else blob

    override = _first_non_blank(
        article.get("subtitle_text"),
        article.get("narration"),
        article.get("narration_script"),
    )
    if override:
        raw_sub = override.strip()
    elif extra:
        raw_sub = f"{title}\n\n{extra}".strip()
    else:
        raw_sub = title.strip()

    ideal_narration_seconds = ideal_narration_seconds_for_article(article)
    has_script_override = bool(override)

    if not use_ideal_narration_policy:
        subtitle_text = raw_sub
        if scene_count is not None:
            n = int(scene_count)
        else:
            n = required_scene_count(audio_seconds=audio_seconds, subtitle_text=subtitle_text)
    elif has_script_override:
        # Pre-composed script from ``compose_video_narration_for_publish``: research + bridges already applied.
        if article.get("narration_research_already_merged"):
            subtitle_text = raw_sub
        else:
            # Hand-written override: merge any new research facts; no generic bridges here.
            subtitle_text = merge_research_into_narration_body(raw_sub, article)
        if scene_count is not None:
            n = int(scene_count)
        else:
            n = max(
                required_scene_count(audio_seconds=ideal_narration_seconds),
                required_scene_count(subtitle_text=subtitle_text),
            )
    elif _AUTO_EXPAND_VIDEO_NARRATION:
        merged = merge_research_into_narration_body(raw_sub, article)
        subtitle_text = pad_narration_with_bridges(merged, ideal_narration_seconds)
        if scene_count is not None:
            n = int(scene_count)
        else:
            n = required_scene_count(subtitle_text=subtitle_text)
    else:
        subtitle_text = merge_research_into_narration_body(raw_sub, article)
        if scene_count is not None:
            n = int(scene_count)
        else:
            n = max(
                required_scene_count(audio_seconds=ideal_narration_seconds),
                required_scene_count(subtitle_text=subtitle_text),
            )
    n = max(MIN_VIDEO_SCENES, n)

    focus = f"{title} — {extra}".strip() if extra else title
    focus_rich = focus
    if bullets:
        ctx = research_digest({"bullets": bullets[:10]}, max_chars=780)
        if ctx:
            focus_rich = f"{focus} — Context: {ctx}"
    if len(focus_rich) > 1000:
        focus_rich = focus_rich[:997] + "…"

    specs = _role_specs_cycle()
    teaching = _n_teaching_points(title, body_for_teaching, n)
    scenes: List[Dict[str, Any]] = []
    for i in range(n):
        role, directive = specs[i % len(specs)]
        tp = teaching[i] if i < len(teaching) else focus
        scenes.append(
            {
                "index": i,
                "role": role,
                "teaching_point": tp,
                "prompt_summary": f"{directive} Story focus: {focus_rich}. Primary fact for this frame: {tp}",
            }
        )

    est_sec = max(
        10.0,
        _narration_word_count(subtitle_text) / max(0.01, NARRATION_WORDS_PER_SECOND_PLANNING),
    )
    return {
        "duration_seconds": int(round(n * 3.6)),
        "scene_count": n,
        "scenes": scenes,
        "subtitle_text": subtitle_text,
        "research_brief": rb,
        "research_digest": research_digest(rb, max_chars=1200) if bullets else "",
        "ideal_narration_seconds": round(float(ideal_narration_seconds), 1),
        "estimated_narration_seconds": round(float(est_sec), 1),
        "narration_expansion_enabled": bool(use_ideal_narration_policy and _AUTO_EXPAND_VIDEO_NARRATION),
        "research_merged_into_narration": bool(
            use_ideal_narration_policy
            and len((subtitle_text or "").strip()) > len((raw_sub or "").strip()) + 12
        ),
    }


def build_render_plan(
    article: Mapping[str, Any],
    *,
    use_ideal_narration_policy: bool = True,
) -> Dict[str, Any]:
    """Describe branding and subtitle mode for the manual Cursor video pipeline (with story pack)."""
    story_pack = build_manual_video_story_arc(
        article, use_ideal_narration_policy=use_ideal_narration_policy
    )
    return {
        "story_pack": story_pack,
        "branding": {
            "breaking_news": True,
            "ai_generated": True,
            "unseen_economy_logo": True,
        },
        "subtitles_mode": "full_summary",
    }


def write_cursor_image_prompts_paste_file(
    out_dir: str,
    prompts: Sequence[Mapping[str, Any]],
    article: Mapping[str, Any],
) -> str:
    """Plain-text file: one block per scene for copy-paste into Cursor's image tool."""
    path = os.path.join(out_dir, "CURSOR_IMAGE_PROMPTS_PASTE.txt")
    n = len(prompts)
    last = max(0, n - 1)
    lines = [
        f"Cursor chat only: use the image tool inside this chat ({n} separate images; "
        f"minimum policy is {MIN_VIDEO_SCENES} scenes).",
        "No local diffusion, no API scripts, no PIL fallbacks — only images you generate here in Cursor chat.",
        "Each prompt asks for one INFORMATIVE beat; roles cycle hook → context → catalyst → reaction → outlook.",
        "Keep the same palette and recurring anchor motifs across every scene so they read as one explainer chain.",
        f"Save as scene0.png … scene{last}.png in this folder.",
    ]
    _rb = article.get("research_brief")
    if isinstance(_rb, dict) and (_rb.get("bullets") or []):
        lines.append(
            "Prompts include a SECONDARY RESEARCH clause — turn those facts into wordless diagrams, maps, and "
            "industry shapes (no readable text in-frame)."
        )
    lines.extend(
        [
            "",
            f"Story: {article.get('title', '')}",
            "",
        ]
    )
    for entry in prompts:
        i = entry.get("scene_index", 0)
        role = entry.get("role", "")
        cont = (entry.get("continuity") or "").strip()
        pr = (entry.get("prompt") or "").strip()
        lines.append("=" * 72)
        lines.append(f"SCENE {i} — {role} (copy from next line until the next ===)")
        lines.append(f"Continuity note: {cont}")
        lines.append("---")
        lines.append(pr)
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def write_cursor_images_readme(
    out_dir: str,
    n_scenes: int,
    article_json_path: str,
) -> str:
    """Short operator steps + example render command."""
    out_abs = os.path.abspath(out_dir)
    art_abs = os.path.abspath(article_json_path)
    readme_path = os.path.join(out_abs, "CURSOR_IMAGES_README.txt")
    scene_paths = " ".join(f'"{out_abs}/scene{i}.png"' for i in range(n_scenes))
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Scene stills: Cursor **chat** image tool only (no local diffusion / no scripts / no fallback).\n\n"
            f"1. Open CURSOR_IMAGE_PROMPTS_PASTE.txt. Generate {n_scenes} images with the image tool in this chat.\n"
            f"2. Save as scene0.png … scene{n_scenes - 1}.png in this folder.\n"
            "3. From the project root, render the final MP4:\n\n"
            "Example (Kokoro + pycaps kinetic + branding):\n"
            f"  python scripts/render_manual_cursor_video.py render "
            f"--images {scene_paths} "
            f'--output "{out_abs}/final.mp4" --article "{art_abs}"\n'
        )
    return readme_path


def write_cursor_operator_bundle(
    out_dir: str,
    article: Mapping[str, Any],
    *,
    use_ideal_narration_policy: bool = True,
) -> tuple[str, str, str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Write ``cursor_video_pack.json``, paste file, and readme for the Cursor-image-tool workflow.
    Does not write ``article.json`` (caller supplies it).
    """
    os.makedirs(out_dir, exist_ok=True)
    plan = build_render_plan(
        article, use_ideal_narration_policy=use_ideal_narration_policy
    )
    story = plan["story_pack"]
    prompts: List[Dict[str, Any]] = list(build_cursor_prompt_pack(story))
    pack_path = os.path.join(out_dir, "cursor_video_pack.json")
    payload = {
        "article": dict(article),
        "render_plan": {k: v for k, v in plan.items() if k != "story_pack"},
        "story_pack": story,
        "cursor_prompts": prompts,
        "images_policy": "cursor_image_tool_only",
    }
    with open(pack_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    paste_path = write_cursor_image_prompts_paste_file(out_dir, prompts, article)
    article_json_path = os.path.join(os.path.abspath(out_dir), "article.json")
    readme_path = write_cursor_images_readme(out_dir, len(prompts), article_json_path)
    return pack_path, paste_path, readme_path, story, prompts


def load_cursor_tool_scene_paths_if_present(work_dir: str, scene_count: int) -> Optional[List[str]]:
    """Return ordered scene image paths if ``scene0``…``scene{n-1}`` exist (.png / .jpg / .jpeg); else None."""
    paths: List[str] = []
    wd = os.path.abspath(work_dir)
    for i in range(int(scene_count)):
        found = None
        for ext in (".png", ".jpg", ".jpeg"):
            p = os.path.join(wd, f"scene{i}{ext}")
            if os.path.isfile(p):
                found = os.path.abspath(p)
                break
        if not found:
            return None
        paths.append(found)
    return paths


def _headline_from_subtitle_text(subtitle_text: str) -> str:
    raw = (subtitle_text or "").strip()
    if not raw:
        return "Breaking News"
    first_block = raw.split("\n\n", 1)[0].strip()
    t = " ".join(first_block.split())
    if not t:
        return "Breaking News"
    if " — " in t:
        return t.split(" — ", 1)[0].strip()
    if ". " in t and len(t) > 72:
        return (t.split(". ", 1)[0].strip() + ".").strip()
    return (t[:96] + "…") if len(t) > 96 else t


def _wrap_subtitle_lines(text: str, max_chars: int) -> List[str]:
    lines = textwrap.wrap(
        text,
        width=max(8, max_chars),
        break_long_words=True,
        break_on_hyphens=True,
    )
    return lines if lines else [text]


def _subtitle_burn_in_lines(text: str, max_chars: int) -> List[Optional[str]]:
    """
    Split on blank lines into paragraphs; wrap each separately.
    ``None`` entries are vertical gaps between paragraphs (headline vs body).
    """
    raw = (text or "").strip()
    if not raw:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", raw) if p.strip()]
    if not paragraphs:
        return []
    out: List[Optional[str]] = []
    for j, p in enumerate(paragraphs):
        if j:
            out.append(None)
        chunk = " ".join(p.split())
        out.extend(_wrap_subtitle_lines(chunk, max_chars))
    return out


def apply_full_summary_subtitles_to_video(
    video_path: str,
    subtitle_text: str,
    output_path: str,
) -> Optional[str]:
    """
    Burn in the full summary as readable wrapped lines for the whole clip duration.
    Landscape (16:9): bottom-centered safe band. Portrait: upper-middle band (legacy).
    """
    if not video_path or not os.path.isfile(video_path):
        print("Subtitles skipped: input video missing.")
        return None
    raw_sub = (subtitle_text or "").strip()
    if not raw_sub:
        print("Subtitles skipped: empty subtitle text.")
        return None
    try:
        from moviepy import CompositeVideoClip, TextClip, VideoFileClip
    except ImportError as e:
        print(f"Subtitles skipped: moviepy not available ({e}).")
        return None

    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    video = VideoFileClip(video_path)
    duration = max(float(video.duration or 0), 0.1)
    w, h = int(video.w), int(video.h)
    landscape = w >= h
    max_width = int(w * (0.82 if landscape else 0.88))
    if landscape:
        y_max = int(h * 0.86)
        y_min = int(h * 0.38)
        available_height = max(120, y_max - y_min)
    else:
        y_bottom_cap = int(h * 0.68)
        y_top_min = int(h * 0.08)
        available_height = max(120, y_bottom_cap - y_top_min)

    font_size = max(22, int(h * (0.038 if landscape else 0.052)))
    lines_with_gaps: List[Optional[str]] = []
    line_height = 1
    paragraph_gap = 1
    while font_size >= 16:
        approx_char = max(7, int(font_size * 0.52))
        max_chars = max(8, max_width // approx_char)
        lines_with_gaps = _subtitle_burn_in_lines(raw_sub, max_chars)
        if not lines_with_gaps:
            lines_with_gaps = _subtitle_burn_in_lines(
                " ".join(raw_sub.split()),
                max_chars,
            )
        line_height = int(font_size * 1.34)
        paragraph_gap = max(10, int(font_size * 0.55))
        text_rows = sum(1 for x in lines_with_gaps if x is not None)
        gap_rows = sum(1 for x in lines_with_gaps if x is None)
        total_h = text_rows * line_height + gap_rows * paragraph_gap
        if total_h <= available_height and text_rows <= 16:
            break
        font_size -= 2

    if not lines_with_gaps:
        fallback = " ".join(raw_sub.split())
        lines_with_gaps = [fallback[:100] + ("…" if len(fallback) > 100 else "")]
        font_size = 22
        line_height = int(font_size * 1.34)
        paragraph_gap = max(10, int(font_size * 0.55))

    text_rows = sum(1 for x in lines_with_gaps if x is not None)
    gap_rows = sum(1 for x in lines_with_gaps if x is None)
    total_h = text_rows * line_height + gap_rows * paragraph_gap
    if landscape:
        y_max = int(h * 0.86)
        y_min = int(h * 0.38)
        y_start = y_max - total_h
        y_start = max(y_min, y_start)
    else:
        y_bottom_cap = int(h * 0.68)
        y_top_min = int(h * 0.08)
        y_start = y_top_min + max(0, (available_height - total_h) // 2)

    subtitle_clips: List[Any] = []
    try:
        y_cursor = y_start
        for line in lines_with_gaps:
            if line is None:
                y_cursor += paragraph_gap
                continue
            tc = TextClip(
                text=line,
                font_size=font_size,
                color="white",
                stroke_color="black",
                stroke_width=max(1, int(font_size * 0.06)),
                method="caption",
                size=(max_width, None),
            )
            tc = tc.with_position(("center", y_cursor)).with_start(0).with_duration(duration)
            subtitle_clips.append(tc)
            y_cursor += line_height

        final = CompositeVideoClip([video, *subtitle_clips]).with_duration(duration)
        final.audio = video.audio
        write_kw: Dict[str, Any] = {
            "codec": "libx264",
            "temp_audiofile": "temp-manual-sub-audio.m4a",
            "remove_temp": True,
            "fps": max(24, int(round(video.fps or 24))),
            "preset": "medium",
            "ffmpeg_params": ["-crf", "18"],
            "logger": None,
        }
        if video.audio is not None:
            write_kw["audio_codec"] = "aac"
        final.write_videofile(out_abs, **write_kw)
        video.close()
        final.close()
        for c in subtitle_clips:
            c.close()
        if os.path.isfile(out_abs):
            return out_abs
    except Exception as e:
        print(f"Subtitle render failed: {e}")
        try:
            video.close()
        except Exception:
            pass
    return None


def build_final_manual_cursor_video(
    image_paths: Sequence[str],
    *,
    output_path: str,
    subtitle_text: str,
    headline: Optional[str] = None,
    subtitles: bool = True,
    branding: bool = True,
    premium_voice_subtitles: bool = False,
    pycaps_kinetic_subtitles: bool = False,
    pycaps_template: str = "dynamic-neon-pop",
    pycaps_video_quality: str = "very_high",
    pycaps_layout_align: str = "bottom",
    pycaps_layout_offset: Optional[float] = 0.0,
    pycaps_preview: bool = False,
    kokoro_voice: Optional[str] = None,
    whisper_model: Optional[str] = None,
    kokoro_speed: float = 1.0,
    video_duration_seconds: Optional[float] = None,
    branding_breaking_label: bool = False,
    thumbnail_intro_path: Optional[str] = None,
    thumbnail_intro_seconds: float = 1.75,
    **render_kw: Any,
) -> Optional[str]:
    """
    Stitch N images (non-premium default: 18s if 5 images, else max(18s, ~3.6s×N); premium stitch follows narration
    unless ``video_duration_seconds`` is set). Optionally burn subtitles, then branding.

    When ``premium_voice_subtitles`` or ``pycaps_kinetic_subtitles`` is True: Kokoro runs first; the stitched
    timeline matches **natural narration length** unless ``video_duration_seconds`` is set (then audio is
    time-stretched to that length). Whisper timings follow the heard audio. Use ``pycaps_kinetic_subtitles`` for
    [pycaps](https://github.com/francozanardi/pycaps) CSS kinetic presets (default ``dynamic-neon-pop``; built-in
    names such as ``word-focus`` are still supported). Otherwise MoviePy burn-in is used. If ``subtitles`` is False and only ``premium_voice_subtitles`` is True (no pycaps),
    narration is added without Whisper/MoviePy timed captions. ``pycaps_kinetic_subtitles`` always enables timed CSS
    captions regardless of ``subtitles``. ``subtitles`` still controls the separate static full-summary burn-in
    (non-premium path). ``headline`` is kept for API compatibility. Branding: AI label + bright logo; optional
    top-left breaking pill via ``branding_breaking_label`` (default False). No headline lower-third bar.
    Optional ``thumbnail_intro_path``: PNG prepended as a silent (or padded) still for ``thumbnail_intro_seconds``
    before the main clip (ffmpeg), matching video resolution and frame rate.
    """
    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    use_premium = bool(premium_voice_subtitles or pycaps_kinetic_subtitles)
    if not subtitles and not branding and not use_premium:
        rk0 = dict(render_kw)
        _sr0 = _scene_duration_ratios_from_subtitle(subtitle_text, len(image_paths))
        if _sr0 is not None:
            rk0.setdefault("scene_duration_ratios", _sr0)
        return render_manual_video_from_images(
            image_paths,
            output_path=out_abs,
            duration_seconds=video_duration_seconds,
            **rk0,
        )

    tmpdir = tempfile.mkdtemp(prefix="manual_cursor_final_")
    try:
        raw = os.path.join(tmpdir, "stitched.mp4")
        rk = dict(render_kw)
        _sr = _scene_duration_ratios_from_subtitle(subtitle_text, len(image_paths))
        if _sr is not None:
            rk.setdefault("scene_duration_ratios", _sr)
        kwav: Optional[str] = None
        fit_premium_audio = False
        if use_premium:
            from premium_voice_subtitles import (
                _ffprobe_duration_seconds,
                apply_premium_voice_and_subtitles,
                narration_text_for_tts,
                synthesize_kokoro_wav,
            )

            narr = narration_text_for_tts(subtitle_text)
            if not narr:
                return None
            kwav = os.path.join(tmpdir, "kokoro_raw.wav")
            if not synthesize_kokoro_wav(
                narr,
                kwav,
                voice=kokoro_voice,
                speed=float(kokoro_speed),
            ):
                return None
            adur = _ffprobe_duration_seconds(kwav)
            if adur is None or adur <= 0:
                return None
            need_scenes = required_scene_count(audio_seconds=float(adur))
            if len(image_paths) < need_scenes:
                print(
                    f"[Manual video] Narration ~{adur:.1f}s needs at least {need_scenes} scene images "
                    f"(min {MIN_VIDEO_SCENES}, ≥1 per {int(AUDIO_SECONDS_PER_SCENE)}s). Got {len(image_paths)}."
                )
                return None
            fit_premium_audio = video_duration_seconds is not None
            stitch_seconds = (
                float(video_duration_seconds) if fit_premium_audio else float(adur)
            )
            stitched = render_manual_video_from_images(
                image_paths,
                output_path=raw,
                duration_seconds=stitch_seconds,
                **rk,
            )
        else:
            stitched = render_manual_video_from_images(
                image_paths,
                output_path=raw,
                duration_seconds=video_duration_seconds,
                **rk,
            )
        if not stitched:
            return None
        current = stitched
        if use_premium:
            if not kwav:
                return None
            premium_out = os.path.join(tmpdir, "premium.mp4")
            # ``--no-subtitles`` skips static paragraph burn-in, not pycaps/Whisper (unless moviepy-only premium).
            burn_timed = bool(pycaps_kinetic_subtitles or (premium_voice_subtitles and subtitles))
            p = apply_premium_voice_and_subtitles(
                current,
                subtitle_text,
                premium_out,
                burn_whisper_subtitles=burn_timed,
                kokoro_voice=kokoro_voice,
                whisper_model=whisper_model,
                kokoro_speed=float(kokoro_speed),
                subtitle_engine="pycaps" if pycaps_kinetic_subtitles else "moviepy",
                pycaps_template=str(pycaps_template or "dynamic-neon-pop"),
                pycaps_video_quality=str(pycaps_video_quality or "very_high"),
                pycaps_layout_align=str(pycaps_layout_align or "bottom"),
                pycaps_layout_offset=pycaps_layout_offset,
                pycaps_preview=bool(pycaps_preview),
                fit_audio_to_video=fit_premium_audio,
                narration_wav_path=kwav,
            )
            if not p:
                return None
            current = p
        elif subtitles:
            sub_path = os.path.join(tmpdir, "with_subtitles.mp4")
            sub = apply_full_summary_subtitles_to_video(current, subtitle_text, sub_path)
            if not sub:
                return None
            current = sub
        final_v = current
        if branding:
            from video_branding import brand_video_for_posting

            branded = os.path.join(tmpdir, "branded.mp4")
            b = brand_video_for_posting(
                current,
                headline=None,
                output_path=branded,
                show_headline_lower_third=False,
                show_breaking_label=bool(branding_breaking_label),
            )
            if not b:
                return None
            final_v = b
        thumb = (thumbnail_intro_path or "").strip()
        if thumb:
            thumb_abs = os.path.abspath(thumb)
            if os.path.isfile(thumb_abs):
                from video_intro import prepend_png_intro_to_video

                with_intro = os.path.join(tmpdir, "with_thumb_intro.mp4")
                merged = prepend_png_intro_to_video(
                    final_v,
                    thumb_abs,
                    with_intro,
                    intro_seconds=float(thumbnail_intro_seconds),
                )
                if merged:
                    final_v = merged
            else:
                print(f"[Thumb intro] PNG not found: {thumb_abs}")
        shutil.copy2(final_v, out_abs)
        return out_abs if os.path.isfile(out_abs) else None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def generate_five_scene_images_for_article(
    article: Mapping[str, Any],
    work_dir: str,
    *,
    topic_theme: Optional[str] = None,
    visual_style: Optional[str] = None,
) -> Optional[List[str]]:
    """
    Scene stills are **not** generated here. Use the **Cursor image tool in chat** with
    ``CURSOR_IMAGE_PROMPTS_PASTE.txt``, then ``load_cursor_tool_scene_paths_if_present`` or pass paths to render.

    Kept for API compatibility; always returns ``None`` (no local / scripted fallback).
    """
    print(
        "[Scenes] Multi-scene images are Cursor-only: use the image tool in Cursor chat with "
        "CURSOR_IMAGE_PROMPTS_PASTE.txt — no local diffusion fallback."
    )
    return None


def run_automated_five_scene_pipeline(
    article: Mapping[str, Any],
    *,
    output_video_path: str,
    work_dir: str,
    headline: Optional[str] = None,
    **render_kw: Any,
) -> Optional[str]:
    """
    Stitch and premium-render using ``scene0``…``scene{n-1}`` (.png/.jpg) already saved under ``work_dir``
    (from the Cursor chat image tool). No image generation.
    """
    story = build_manual_video_story_arc(article)
    n = int(story.get("scene_count") or MIN_VIDEO_SCENES)
    paths = load_cursor_tool_scene_paths_if_present(work_dir, n)
    if not paths:
        print(
            f"[Scenes] Missing scene images in {work_dir!r} (need scene0 … scene{n - 1}). "
            "Generate them in Cursor chat only; no fallback."
        )
        return None
    sub = str(story.get("subtitle_text") or "")
    if headline is not None:
        head = headline.strip() or None
    else:
        t = _first_non_blank(article.get("title"), article.get("headline"))
        head = t if t else None
    return build_final_manual_cursor_video(
        paths,
        output_path=output_video_path,
        subtitle_text=sub,
        headline=head,
        **render_kw,
    )


_FINANCE_IMAGE_GUARDRAILS = (
    "Professional finance-news editorial still: institutions, data, policy, markets, or macro context only. "
    "Avoid unrelated fantasy, memes, or decorative clutter. No company logos, no watermarks, no legible headlines, "
    "tickers, or dates in-frame — viewer context comes from video subtitles/overlays."
)

# Push image models toward explainer-style stills (one teachable idea per frame), not generic mood shots.
_FINANCE_EXPLAINER_POLICY = (
    "EXPLAINER STILL (mandatory): This image must be INFORMATIVE — a viewer should grasp ONE concrete idea about "
    "the story from this frame alone. Prefer diagram-like clarity: clear focal subject, cause-to-effect flow "
    "(arrows or light trails between abstract shapes), or a split before/after composition. "
    "Use recurring simplified anchor motifs across all scenes in the pack (same stylized globe, energy droplet, bond beam, "
    "or equity step motif where the story implies it) so the set reads as one chained explanation, not random "
    "unrelated wallpapers. Do not default to a generic trading floor unless it directly illustrates the mechanism named in "
    "the story focus. All numbers and labels must stay blurred or illegible; convey meaning through layout and "
    "metaphor, not readable text."
)

_MEMORY_SEMICON_PHRASES = (
    "micron",
    "flash memory",
    "memory chip",
    "memory cycle",
    "memory sector",
    "semiconductor memory",
    "memory producer",
    "sk hynix",
    "samsung electronics",
    "solid state drive",
    "photolithography",
    "semiconductor fab",
    "chipmaker",
    "chip maker",
    "memory glut",
)
_MEMORY_SEMICON_TOKEN_RE = re.compile(
    r"\b(dram|nand|hbm|ssd|dimm|wafer|hynix)\b",
    re.IGNORECASE,
)

_ENERGY_PETROCHEM_PHRASES = (
    "strait of hormuz",
    "persian gulf",
    "opec",
    "brent",
    "wti",
    "crude oil",
    "oil price",
    "oil prices",
    "petrochemical",
    "refinery",
    "lng",
    "natural gas",
    "shipping lane",
    "tanker",
    "plastics",
    "polymer",
    "feedstock",
    "crack spread",
    "energy inflation",
)
_ENERGY_PETROCHEM_TOKEN_RE = re.compile(
    r"\b(hormuz|opec|brent|wti|lng|crude|petro|refiner|tanker|polymer|feedstock)\b",
    re.IGNORECASE,
)


def _story_pack_inference_text(story_pack: Mapping[str, Any]) -> str:
    focus = str(story_pack.get("subtitle_text") or "")
    parts = [focus.lower()]
    for scene in story_pack.get("scenes") or []:
        parts.append(str(scene.get("prompt_summary") or "").lower())
    return " ".join(parts)


def infer_visual_domain_from_story(story_pack: Mapping[str, Any]) -> str:
    """
    Rough topic bucket for image prompts. ``memory_semiconductor`` unlocks DRAM/fab-specific concrete nouns;
    ``energy_petrochemical`` unlocks shipping chokepoints, refineries, and polymer-chain metaphors.
    Phrases catch obvious stories; short tokens use word boundaries (avoids matching \"dram\" in \"dramatic\").
    """
    blob = _story_pack_inference_text(story_pack).lower()
    for phrase in _MEMORY_SEMICON_PHRASES:
        if phrase in blob:
            return "memory_semiconductor"
    if _MEMORY_SEMICON_TOKEN_RE.search(blob):
        return "memory_semiconductor"
    for phrase in _ENERGY_PETROCHEM_PHRASES:
        if phrase in blob:
            return "energy_petrochemical"
    if _ENERGY_PETROCHEM_TOKEN_RE.search(blob):
        return "energy_petrochemical"
    return "general"


def _memory_concrete_visual_anchors() -> str:
    return (
        "Concrete still-safe visuals: DRAM module and DIMM-slot silhouettes (no labels); Ball-grid and memory-package "
        "outlines; wafer sheen and soft photolithography streaks; clean-room haze with gantry and glove-port shapes "
        "(no logos); commodity memory pricing as abstract heat map / liquidity mesh (any glyphs or numerals smeared "
        "and unreadable only)."
    )


def _general_concrete_visual_anchors() -> str:
    return (
        "Concrete still-safe visuals: simple flowchart nodes linked by arrows or ribbons (no readable labels); "
        "institutional terminal strips only when they support a named mechanism; policy-rate lattice; "
        "credit-spread widening as two diverging bands; cross-border corridor maps with one highlighted chokepoint "
        "or region; macro breakeven haze (ticks and numbers unreadable smudges only)."
    )


def _energy_petrochemical_visual_anchors() -> str:
    return (
        "Concrete still-safe visuals for energy macro: narrow strait / chokepoint map silhouette with one glowing "
        "pinch (no country names legible); VLCC or product-tanker outlines on a sea lane ribbon; refinery column "
        "and flare-stack shapes as abstract silhouettes; pipeline manifold as linked tubes; crude vs refined split "
        "as two fluid fields; polymer chain as beaded strand or resin pellet stream beside an oil droplet motif; "
        "freight cost as stacked route bands; any numerals or port codes smeared and unreadable only."
    )


def _scene_visual_beat(role: str, domain: str) -> str:
    role = (role or "").strip().lower()
    if domain == "energy_petrochemical":
        beats = {
            "hook": (
                "Scene beat (hook): twin-thesis clarity — oil/energy shock AND downstream plastics or refined products "
                "as linked silhouettes (droplet + polymer strand or refinery + consumer-goods haze); one glance shows "
                "why the headline pairs them."
            ),
            "context": (
                "Scene beat (context): physical system map — where barrels move (sea lane ribbon, pinch-point strait "
                "glow) and where molecules upgrade (refinery towers, cracker metaphor as heat plume). No readable "
                "geography labels."
            ),
            "catalyst": (
                "Scene beat (catalyst): disruption to flow — blockage, sanction beam, outage flare, or freight spike "
                "as a single sharp visual interrupt on the route schematic."
            ),
            "reaction": (
                "Scene beat (reaction): joint repricing — brent/wti-style twin curves or bands diverging, crack-spread "
                "wedge opening, consumer inflation haze lifting off the polymer lane; direction of stress must read "
                "without legible tickers."
            ),
            "outlook": (
                "Scene beat (outlook): forward watchlist — inventory floats, OPEC-style supply dial (abstract), "
                "policy storage release, and plastics demand as four distinct symbolic shapes; dates/digits illegible."
            ),
        }
        return beats.get(role, beats["hook"])
    if domain == "memory_semiconductor":
        beats = {
            "hook": (
                "Scene beat (hook): immediate headline gravity — memory-sector stress and downward pressure; lean on "
                "DRAM/DIMM silhouettes and bearish light."
            ),
            "context": (
                "Scene beat (context): sector backdrop — fabs, long-haul supply lanes, large-cap peer grid as abstract "
                "glass layers (no tickers legible)."
            ),
            "catalyst": (
                "Scene beat (catalyst): supply glut / inventory-cycle metaphor — stacked pallet masses, warehouse "
                "haze, channel pressure, dock queues (no brand crates or readable shipping text)."
            ),
            "reaction": (
                "Scene beat (reaction): index and peer repricing — S&P-linked valuation strip as forward-multiple "
                "ribbons and dispersion fans (numerals deliberately unreadable)."
            ),
            "outlook": (
                "Scene beat (outlook): next catalyst — earnings and guidance imagined as calendar blocks and runway "
                "bands (all dates and digits blurred or illegible); soft glow on the approaching decision window."
            ),
        }
    else:
        beats = {
            "hook": (
                "Scene beat (hook): state the HEADLINE THESIS in one visual — a single unmistakable metaphor for what "
                "broke or shifted (e.g. fracture through a calm chart plane, pressure on a pipeline, policy lever "
                "tilting). Not atmosphere-only; the composition must encode the claim implied by the story focus."
            ),
            "context": (
                "Scene beat (context): map the MECHANISM SPACE — who/where/which channels matter: show linked "
                "regions, institutions, or funding routes as a simple schematic (corridors, nodes, counterparties as "
                "abstract blocks). The viewer should see how pieces of the story connect before the trigger."
            ),
            "catalyst": (
                "Scene beat (catalyst): isolate THE TRIGGER as one sharp event — a data print shockwave, policy "
                "decision hammer, filing stack pulse, or supply disruption spike. One dominant cause, not a collage."
            ),
            "reaction": (
                "Scene beat (reaction): show MARKET REPRICING — split or dual-field composition: risk-off vs "
                "risk-on tone, widening spreads, volatility bloom, or equity path bending; convey direction of move "
                "without legible tickers."
            ),
            "outlook": (
                "Scene beat (outlook): FORWARD CATALYSTS as a small distinct set of symbolic elements the viewer "
                "can count (e.g. oil shape, rates beam, calendar blocks, policy podium silhouette) — each shape a "
                "different thing to watch; dates and digits illegible."
            ),
        }
    return beats.get(role, beats["hook"])


def _scene_information_job(role: str) -> str:
    """One-line objective for the image model: what this frame must teach."""
    role = (role or "").strip().lower()
    jobs = {
        "hook": "Information job: After this frame, the viewer names what happened or what the story is about.",
        "context": "Information job: After this frame, the viewer understands the setup — regions, actors, or channels involved.",
        "catalyst": "Information job: After this frame, the viewer identifies the specific trigger that moved markets or policy.",
        "reaction": "Information job: After this frame, the viewer sees how prices, risk, or sentiment shifted in response.",
        "outlook": "Information job: After this frame, the viewer knows what to watch next (several forward risks or events, wordlessly).",
    }
    return jobs.get(role, jobs["hook"])


def build_cursor_prompt_pack(story_pack: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Build one Cursor image prompt per scene; each entry includes continuity notes."""
    scenes: List[Mapping[str, Any]] = list(story_pack.get("scenes") or [])
    if len(scenes) < MIN_VIDEO_SCENES:
        raise ValueError(
            f"build_cursor_prompt_pack requires at least {MIN_VIDEO_SCENES} scenes, got {len(scenes)}"
        )
    focus = _first_non_blank(story_pack.get("subtitle_text"), default="Market update")
    focus_flat = " ".join(focus.split())
    domain = infer_visual_domain_from_story(story_pack)
    if domain == "memory_semiconductor":
        anchors = _memory_concrete_visual_anchors()
    elif domain == "energy_petrochemical":
        anchors = _energy_petrochemical_visual_anchors()
    else:
        anchors = _general_concrete_visual_anchors()

    digest = str(story_pack.get("research_digest") or "").strip()
    research_clause = ""
    if digest:
        research_clause = (
            "SECONDARY RESEARCH for this story (use for accurate metaphors and composition — show as diagrams, "
            "maps, process flows, industry silhouettes; never readable text, logos, tickers, or precise numbers in-frame): "
            f'"{digest}" '
        )

    entries: List[Dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        if i == 0:
            continuity = (
                "First scene: establish the same single finance-news event, explainer visual language, and recurring "
                "anchor motifs; all following scenes continue this one story thread in sequence."
            )
        else:
            continuity = (
                f"Continues the same news story from the previous scene (scene {i - 1}): "
                "reuse the same palette and recurring simplified anchors (globe, energy, rates, equity motifs as "
                "appropriate); only advance the narrative beat—each frame teaches the next logical idea."
            )
        role = str(scene.get("role", ""))
        summary = str(scene.get("prompt_summary", ""))
        beat = _scene_visual_beat(role, domain)
        info_job = _scene_information_job(role)
        tp = str(scene.get("teaching_point") or "").strip() or focus_flat[:220]
        prompt = (
            f"{_FINANCE_IMAGE_GUARDRAILS} {_FINANCE_EXPLAINER_POLICY} {anchors} {research_clause}{beat} {info_job} "
            f'Scene {i} ({role}): the full story context is "{focus_flat}". '
            f'PRIMARY FACT THIS FRAME MUST VISUALLY EXPLAIN (dominant read, not background): "{tp}". {summary}'
        )
        entries.append(
            {
                "scene_index": int(scene.get("index", i)),
                "role": role,
                "continuity": continuity,
                "visual_domain": domain,
                "prompt": prompt,
            }
        )

    return entries


def _ffmpeg_concat_copy(concat_list_path: str, output_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list_path,
            "-c",
            "copy",
            output_path,
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )


def _ffmpeg_concat_reencode(concat_list_path: str, output_path: str, fps: int) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list_path,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            output_path,
        ],
        check=True,
        capture_output=True,
        timeout=600,
    )


def _scene_duration_ratios_from_subtitle(subtitle_text: str, n: int) -> Optional[List[float]]:
    """
    Per-scene fractions of the timeline (sum to 1) derived from subtitle copy so visuals can
    track story beats instead of equal slices per image.

    Supports: exactly ``n`` paragraphs; headline + body (two paragraphs) split into ``n-1`` body
    slices plus headline; or one paragraph split into ``n`` sequential chunks.
    """
    if n < 1:
        return None
    raw = (subtitle_text or "").strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split("\n\n") if p.strip()]
    virtual: List[str] = []
    if len(parts) == n:
        virtual = parts
    elif len(parts) == 2 and n >= 2:
        head, body = parts[0], parts[1]
        if len(body) < 32:
            return None
        slots = n - 1
        q = max(8, len(body) // slots)
        virtual = [head]
        for j in range(slots):
            start = j * q
            end = (j + 1) * q if j < slots - 1 else len(body)
            virtual.append(body[start:end])
    elif len(parts) == 1 and n >= 1:
        body = parts[0]
        if len(body) < max(40, n * 8):
            return None
        q = max(8, len(body) // n)
        virtual = []
        for i in range(n):
            start = i * q
            end = (i + 1) * q if i < n - 1 else len(body)
            virtual.append(body[start:end])
    else:
        return None
    w = [max(12, len(p)) for p in virtual]
    t = float(sum(w))
    if t <= 0:
        return None
    return [x / t for x in w]


def _write_concat_demuxer_list(clip_paths: Sequence[str], list_path: str) -> None:
    with open(list_path, "w", encoding="utf-8") as f:
        for p in clip_paths:
            posix = os.path.abspath(p).replace("\\", "/")
            posix = posix.replace("'", "'\\''")
            f.write(f"file '{posix}'\n")


def render_manual_video_from_images(
    image_paths: Sequence[str],
    *,
    output_path: str,
    duration_seconds: Optional[float] = None,
    width: int = 1920,
    height: int = 1080,
    effect: str = "static",
    fps: int = 30,
    keep_temp_clips: bool = False,
    scene_duration_ratios: Optional[Sequence[float]] = None,
) -> Optional[str]:
    """
    Stitch one or more images into one MP4.     Each image gets an equal slice of the timeline (default **static** frame; pass ``effect='zoom'`` for Ken Burns).
    If ``duration_seconds`` is None: **18s** when there are 5 images (legacy default), otherwise
    **max(18s, 3.6s×N)** so longer explainer packs get proportionally longer base timelines.
    Pass ``scene_duration_ratios`` (length ``n``, positive, normalized to sum 1) to weight scene
    lengths by story beats instead of equal splits.
    Default frame is cinematic landscape **1920×1080** (16:9).
    """
    paths = [os.path.abspath(p) for p in image_paths]
    n = len(paths)
    if n < 1:
        raise ValueError("render_manual_video_from_images requires at least one image")
    for p in paths:
        if not os.path.isfile(p):
            print(f"Missing image: {p}")
            return None

    if duration_seconds is None:
        total = 18.0 if n == 5 else max(18.0, float(n) * 3.6)
    else:
        total = float(duration_seconds)
    per_scene = total / float(n)
    scene_durs: Optional[List[float]] = None
    if (
        scene_duration_ratios is not None
        and len(scene_duration_ratios) == n
        and all(float(x) > 0 for x in scene_duration_ratios)
    ):
        rs = [float(x) for x in scene_duration_ratios]
        s = sum(rs)
        if s > 0:
            rs = [x / s for x in rs]
            raw_d = [total * r for r in rs]
            floor = max(0.35, min(1.2, total / float(max(n * 4, 1))))
            adj = [max(floor, d) for d in raw_d]
            scale = total / sum(adj)
            scene_durs = [d * scale for d in adj]
    tmpdir = tempfile.mkdtemp(prefix="manual_cursor_vid_")
    clip_paths: List[str] = []
    try:
        for i, img in enumerate(paths):
            clip_out = os.path.join(tmpdir, f"scene_{i}.mp4")
            dur_i = scene_durs[i] if scene_durs else per_scene
            clip = image_to_video_clip(
                img,
                output_path=clip_out,
                duration_seconds=dur_i,
                width=width,
                height=height,
                effect=effect,
                fps=fps,
            )
            if not clip or not os.path.isfile(clip):
                return None
            clip_paths.append(os.path.abspath(clip))

        list_path = os.path.join(tmpdir, "concat.txt")
        _write_concat_demuxer_list(clip_paths, list_path)

        out_abs = os.path.abspath(output_path)
        parent = os.path.dirname(out_abs)
        if parent:
            os.makedirs(parent, exist_ok=True)

        try:
            _ffmpeg_concat_copy(list_path, out_abs)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                _ffmpeg_concat_reencode(list_path, out_abs, fps)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                if isinstance(e, FileNotFoundError):
                    print("ffmpeg not found. Install ffmpeg and add it to PATH:")
                    print("  https://ffmpeg.org/download.html")
                return None

        if os.path.isfile(out_abs):
            return out_abs
    finally:
        if not keep_temp_clips and os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)

    return None
