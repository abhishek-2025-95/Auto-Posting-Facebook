"""
Kokoro TTS (pykokoro) narration + OpenAI Whisper timed subtitles for manual Cursor videos.

Install (optional): pip install pykokoro soundfile openai-whisper
Requires ffmpeg on PATH. First Whisper run downloads model weights.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    from config import KOKORO_VOICE as _DEFAULT_KOKORO_VOICE
    from config import WHISPER_MODEL as _DEFAULT_WHISPER_MODEL
except ImportError:
    _DEFAULT_KOKORO_VOICE = "af_bella"
    _DEFAULT_WHISPER_MODEL = "small"


def narration_text_for_tts(subtitle_text: str) -> str:
    """Flatten subtitle pack copy for speech; paragraph breaks become Kokoro SSMD sentence pauses."""
    t = (subtitle_text or "").strip()
    if not t:
        return ""
    t = t.replace("\n\n", "...s ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _ffprobe_duration_seconds(path: str) -> Optional[float]:
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if r.returncode != 0:
            return None
        return float(r.stdout.strip())
    except (ValueError, subprocess.SubprocessError, OSError):
        return None


def _atempo_filter_chain(speed_factor: float) -> str:
    """
    ``speed_factor`` > 1 = faster playback = shorter duration.
    ffmpeg atempo must stay between 0.5 and 2.0 per filter.
    """
    parts: List[str] = []
    r = float(speed_factor)
    while r > 2.0 + 1e-6:
        parts.append("atempo=2.0")
        r /= 2.0
    while r < 0.5 - 1e-6:
        parts.append("atempo=0.5")
        r /= 0.5
    parts.append(f"atempo={r:.6f}")
    return ",".join(parts)


def fit_wav_to_duration_ffmpeg(in_wav: str, out_wav: str, target_seconds: float) -> bool:
    """Stretch/shrink WAV so its duration matches ``target_seconds`` (within ffmpeg limits)."""
    in_d = _ffprobe_duration_seconds(in_wav)
    if in_d is None or in_d <= 0 or target_seconds <= 0:
        return False
    ratio = in_d / target_seconds
    parent = os.path.dirname(os.path.abspath(out_wav))
    if parent:
        os.makedirs(parent, exist_ok=True)
    if abs(ratio - 1.0) < 0.02:
        shutil.copy2(in_wav, out_wav)
        return os.path.isfile(out_wav)
    chain = _atempo_filter_chain(ratio)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        in_wav,
        "-af",
        chain,
        out_wav,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return os.path.isfile(out_wav)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extend_or_trim_video_duration_ffmpeg(in_mp4: str, out_mp4: str, target_seconds: float) -> bool:
    """
    Make ``out_mp4`` match ``target_seconds`` by cloning the last frame (extend) or trimming (shorter).
    Used so the visual timeline matches natural narration length without time-stretching speech.
    """
    cur = _ffprobe_duration_seconds(in_mp4)
    if cur is None or target_seconds <= 0:
        return False
    out_abs = os.path.abspath(out_mp4)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if abs(cur - target_seconds) < 0.08:
        shutil.copy2(os.path.abspath(in_mp4), out_abs)
        return os.path.isfile(out_abs)
    if target_seconds < cur - 0.05:
        for cmd in (
            [
                "ffmpeg",
                "-y",
                "-i",
                in_mp4,
                "-t",
                f"{target_seconds:.6f}",
                "-c",
                "copy",
                out_abs,
            ],
            [
                "ffmpeg",
                "-y",
                "-i",
                in_mp4,
                "-t",
                f"{target_seconds:.6f}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                out_abs,
            ],
        ):
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=600)
                if os.path.isfile(out_abs):
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False
    pad = target_seconds - cur
    vf = f"tpad=stop_mode=clone:stop_duration={pad:.6f}"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        in_mp4,
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        out_abs,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        return os.path.isfile(out_abs)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def synthesize_kokoro_wav(
    text: str,
    out_wav: str,
    *,
    voice: Optional[str] = None,
    speed: float = 1.0,
) -> Optional[str]:
    """Render narration with Kokoro via pykokoro. Returns path or None."""
    if not text.strip():
        return None
    try:
        import soundfile as sf
        from pykokoro import GenerationConfig, KokoroPipeline, PipelineConfig
    except ImportError as e:
        print(f"[Premium voice] Kokoro skipped: install pykokoro and soundfile ({e}).")
        return None

    voice_id = (voice or _DEFAULT_KOKORO_VOICE or "af_bella").strip()
    parent = os.path.dirname(os.path.abspath(out_wav))
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        pipe = KokoroPipeline(
            PipelineConfig(
                voice=voice_id,
                generation=GenerationConfig(lang="en-us", speed=float(speed)),
            )
        )
        result = pipe.run(text)
        sf.write(out_wav, result.audio, int(result.sample_rate))
    except Exception as e:
        print(f"[Premium voice] Kokoro synthesis failed: {e}")
        return None
    return out_wav if os.path.isfile(out_wav) else None


def mux_video_and_wav(video_mp4: str, wav_path: str, out_mp4: str) -> Optional[str]:
    """
    Replace/add audio track on video from WAV (AAC).

    Matches stream lengths before mux: if the stitched video is shorter than the WAV (common
    after concat rounding), the video is extended with a frozen last frame so narration is not
    clipped and Whisper-based captions stay aligned. If video is longer, the WAV is padded with
    a short silence tail.
    """
    out_abs = os.path.abspath(out_mp4)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    vd = _ffprobe_duration_seconds(video_mp4)
    ad = _ffprobe_duration_seconds(wav_path)
    work_v = video_mp4
    work_w = wav_path
    tmpd: Optional[str] = None

    try:
        if vd is not None and ad is not None and vd > 0 and ad > 0:
            if ad > vd + 0.06:
                tmpd = tempfile.mkdtemp(prefix="mux_vmatch_")
                tmpv = os.path.join(tmpd, "v_aligned.mp4")
                if extend_or_trim_video_duration_ffmpeg(video_mp4, tmpv, ad):
                    work_v = tmpv
            elif vd > ad + 0.06:
                if tmpd is None:
                    tmpd = tempfile.mkdtemp(prefix="mux_amatch_")
                tmpw = os.path.join(tmpd, "a_padded.wav")
                pad = vd - ad
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            wav_path,
                            "-af",
                            f"apad=pad_dur={pad:.6f}",
                            "-c:a",
                            "pcm_s16le",
                            tmpw,
                        ],
                        check=True,
                        capture_output=True,
                        timeout=300,
                    )
                    if os.path.isfile(tmpw):
                        work_w = tmpw
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            work_v,
            "-i",
            work_w,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            out_abs,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        return out_abs if os.path.isfile(out_abs) else None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[Premium voice] mux failed: {e}")
        return None
    finally:
        if tmpd:
            shutil.rmtree(tmpd, ignore_errors=True)


def _pseudo_words_from_text(text: str, t0: float, t1: float) -> List[Dict[str, Any]]:
    words = [w for w in text.replace("\n", " ").split() if w]
    if not words:
        return []
    span = max(0.08, float(t1) - float(t0))
    n = len(words)
    step = span / n
    out: List[Dict[str, Any]] = []
    for i, w in enumerate(words):
        ws = t0 + i * step
        we = t0 + (i + 1) * step
        out.append({"word": w, "start": float(ws), "end": float(we)})
    return out


def _chunk_word_timings(
    items: List[Dict[str, Any]],
    *,
    max_words: int = 5,
    max_span_sec: float = 1.65,
) -> List[Dict[str, Any]]:
    """Group word-level timings into short on-screen cues (more updates = more dynamic)."""
    if not items:
        return []
    cues: List[Dict[str, Any]] = []
    i = 0
    while i < len(items):
        chunk = [items[i]]
        i += 1
        while i < len(items) and len(chunk) < max_words:
            prospective = items[i]["end"] - chunk[0]["start"]
            if prospective <= max_span_sec:
                chunk.append(items[i])
                i += 1
            else:
                break
        cues.append(
            {
                "start": float(chunk[0]["start"]),
                "end": float(chunk[-1]["end"]),
                "text": " ".join(x["word"] for x in chunk),
            }
        )
    for j in range(len(cues) - 1):
        if cues[j]["end"] > cues[j + 1]["start"]:
            cues[j]["end"] = max(cues[j]["start"], cues[j + 1]["start"] - 0.03)
    return cues


def _whisper_result_to_display_cues(result: dict) -> List[Dict[str, Any]]:
    """Flatten Whisper segments + word timestamps into timed caption cues."""
    all_words: List[Dict[str, Any]] = []
    for s in result.get("segments") or []:
        t0 = float(s.get("start", 0.0))
        t1 = float(s.get("end", 0.0))
        raw_text = (s.get("text") or "").strip()
        seg_words: List[Dict[str, Any]] = []
        for w in s.get("words") or []:
            wt = (w.get("word") or "").strip()
            if not wt:
                continue
            try:
                seg_words.append(
                    {
                        "word": wt,
                        "start": float(w["start"]),
                        "end": float(w["end"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        if not seg_words and raw_text:
            seg_words = _pseudo_words_from_text(raw_text, t0, t1)
        all_words.extend(seg_words)
    if not all_words:
        cues: List[Dict[str, Any]] = []
        for s in result.get("segments") or []:
            txt = (s.get("text") or "").strip()
            if not txt:
                continue
            cues.append(
                {
                    "start": float(s.get("start", 0.0)),
                    "end": float(s.get("end", 0.0)),
                    "text": txt,
                }
            )
        return cues
    return _chunk_word_timings(all_words, max_words=5, max_span_sec=1.9)


def transcribe_whisper_full_result(
    audio_wav_path: str,
    *,
    model_size: Optional[str] = None,
    initial_prompt: Optional[str] = None,
) -> Optional[dict]:
    """Run Whisper with word timestamps; return the raw result dict (for pycaps JSON export)."""
    try:
        import whisper
    except ImportError as e:
        print(f"[Premium voice] Whisper skipped: install openai-whisper ({e}).")
        return None

    size = (model_size or _DEFAULT_WHISPER_MODEL or "small").strip()
    try:
        model = whisper.load_model(size)
        t_kw: Dict[str, Any] = dict(
            word_timestamps=True,
            fp16=False,
            verbose=False,
        )
        hint = (initial_prompt or "").strip()
        if hint:
            # Steers recognition toward Kokoro’s script so captions track speech better.
            t_kw["initial_prompt"] = hint[:450]
        return model.transcribe(audio_wav_path, **t_kw)
    except Exception as e:
        print(f"[Premium voice] Whisper transcription failed: {e}")
        return None


def whisper_raw_result_to_pycaps_whisper_json(data: dict) -> dict:
    """
    Build a JSON object compatible with pycaps ``--transcript-format whisper_json``
    (segments with per-word start/end; pseudo-words when Whisper omits word timings).
    """
    lang = data.get("language")
    language = lang if isinstance(lang, str) and lang.strip() else "en"
    segments_out: List[Dict[str, Any]] = []
    for i, s in enumerate(data.get("segments") or []):
        if not isinstance(s, dict):
            continue
        t0 = float(s.get("start", 0.0))
        t1 = float(s.get("end", 0.0))
        text = (s.get("text") or "").strip()
        words_out: List[Dict[str, Any]] = []
        for w in s.get("words") or []:
            if not isinstance(w, dict):
                continue
            wt = str(w.get("word", w.get("text", ""))).strip()
            if not wt:
                continue
            try:
                words_out.append(
                    {
                        "word": wt,
                        "start": float(w["start"]),
                        "end": float(w["end"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        if not words_out and text:
            for pw in _pseudo_words_from_text(text, t0, t1):
                words_out.append(
                    {"word": pw["word"], "start": pw["start"], "end": pw["end"]}
                )
        if not words_out:
            continue
        if not text:
            text = " ".join(str(x["word"]) for x in words_out)
        segments_out.append(
            {
                "id": s.get("id", i),
                "start": t0,
                "end": t1,
                "text": text,
                "words": words_out,
            }
        )
    return {"language": language, "segments": segments_out}


def transcribe_whisper_segments(
    audio_wav_path: str,
    *,
    model_size: Optional[str] = None,
    initial_prompt: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Run Whisper on WAV; return short display cues (word-chunked when timestamps exist)."""
    result = transcribe_whisper_full_result(
        audio_wav_path,
        model_size=model_size,
        initial_prompt=initial_prompt,
    )
    if not result:
        return []
    cues = _whisper_result_to_display_cues(result)
    if cues:
        print(f"[Premium subs] Dynamic captions: {len(cues)} timed cues (word-level chunking).")
    return cues


# Bundled preset: full JSON config (CSS + pop_in on words). CLI uses --config, not --template.
_BUNDLED_PYCAPS_CONFIGS = {
    "dynamic-neon-pop": os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pycaps_dynamic_neon_pop",
        "pycaps.config.json",
    ),
}


def _resolve_pycaps_executable() -> Optional[str]:
    """Console script next to ``sys.executable``, else ``pycaps`` on PATH."""
    from pathlib import Path

    bindir = Path(sys.executable).resolve().parent
    for name in ("pycaps.exe", "pycaps"):
        p = bindir / name
        if p.is_file():
            return str(p)
    return shutil.which("pycaps")


def _run_pycaps_json_config_pipeline(
    input_mp4: str,
    whisper_json_path: str,
    output_mp4: str,
    *,
    config_path: str,
    video_quality: str,
    layout_align: str,
    layout_offset: Optional[float],
    preview: bool,
) -> Optional[str]:
    """
    pycaps ``render`` CLI omits ``with_input_video`` when ``--config`` is used (library bug); build the pipeline
    in-process so input + whisper JSON are wired correctly.
    """
    try:
        from pycaps.cli.render_cli import _build_layout_options, _parse_preview
        from pycaps.common import VideoQuality
        from pycaps.layout import VerticalAlignmentType
        from pycaps.pipeline.json_config_loader import JsonConfigLoader
        from pycaps.transcriber import TranscriptFormat
    except ImportError:
        return None

    out_abs = os.path.abspath(output_mp4)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    cfg = os.path.abspath(config_path)
    builder = JsonConfigLoader(cfg).load(False)
    builder = builder.with_input_video(os.path.abspath(input_mp4))
    builder = builder.with_output_video(out_abs)
    builder = builder.with_transcription_file(
        os.path.abspath(whisper_json_path),
        TranscriptFormat.WHISPER_JSON,
    )

    vq_key = (video_quality or "very_high").strip().lower().replace("-", "_")
    vq_map = {
        "low": VideoQuality.LOW,
        "middle": VideoQuality.MIDDLE,
        "high": VideoQuality.HIGH,
        "very_high": VideoQuality.VERY_HIGH,
    }
    builder = builder.with_video_quality(vq_map.get(vq_key, VideoQuality.VERY_HIGH))

    align_key = (layout_align or "bottom").strip().lower()
    align_map = {
        "bottom": VerticalAlignmentType.BOTTOM,
        "center": VerticalAlignmentType.CENTER,
        "top": VerticalAlignmentType.TOP,
    }
    va = align_map.get(align_key, VerticalAlignmentType.BOTTOM)
    off = float(layout_offset) if layout_offset is not None else 0.0
    builder = builder.with_layout_options(_build_layout_options(builder, va, off))

    preview_time = _parse_preview(preview, None)
    pipeline = builder.build(preview_time=preview_time)
    pipeline.run()
    return out_abs if os.path.isfile(out_abs) else None


def run_pycaps_kinetic_render(
    input_mp4: str,
    whisper_json_path: str,
    output_mp4: str,
    *,
    template: str = "dynamic-neon-pop",
    video_quality: str = "very_high",
    layout_align: str = "bottom",
    layout_offset: Optional[float] = 0.0,
    preview: bool = False,
) -> Optional[str]:
    """
    Burn kinetic CSS subtitles via the ``pycaps`` CLI ([pycaps](https://github.com/francozanardi/pycaps)).
    Preset ``dynamic-neon-pop`` uses the bundled ``pycaps_dynamic_neon_pop/pycaps.config.json`` (neon active word,
    Montserrat/Inter, PopIn per word). Any other ``template`` value is passed as ``--template`` (e.g. word-focus).
    Requires ``pip install 'pycaps[base] @ git+https://github.com/francozanardi/pycaps.git'`` and ffmpeg.
    """
    exe = _resolve_pycaps_executable()
    if not exe:
        print(
            "[Premium subs] pycaps executable not found. Install with:\n"
            '  pip install "pycaps[base] @ git+https://github.com/francozanardi/pycaps.git"'
        )
        return None
    out_abs = os.path.abspath(output_mp4)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    preset_key = (template or "").strip().lower()
    config_path = _BUNDLED_PYCAPS_CONFIGS.get(preset_key)
    if config_path and os.path.isfile(config_path):
        try:
            done = _run_pycaps_json_config_pipeline(
                input_mp4,
                whisper_json_path,
                output_mp4,
                config_path=config_path,
                video_quality=video_quality,
                layout_align=layout_align,
                layout_offset=layout_offset,
                preview=preview,
            )
            if done:
                return done
        except Exception as ex:
            print(f"[Premium subs] pycaps in-process render failed: {ex}")
        print("[Premium subs] pycaps JSON-config render failed (CLI --config is broken for input video).")
        return None

    cmd: List[str] = [
        exe,
        "render",
        "--input",
        os.path.abspath(input_mp4),
        "--output",
        out_abs,
        "--transcript",
        os.path.abspath(whisper_json_path),
        "--transcript-format",
        "whisper_json",
        "--video-quality",
        video_quality,
        "--layout-align",
        layout_align,
        "--template",
        template,
    ]
    if layout_offset is not None:
        cmd.extend(["--layout-align-offset", str(float(layout_offset))])
    if preview:
        cmd.append("--preview")
    try:
        subprocess.run(cmd, check=True, timeout=7200)
    except FileNotFoundError:
        print(f"[Premium subs] pycaps failed to start: {exe!r}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[Premium subs] pycaps render failed (exit {e.returncode}).")
        return None
    except subprocess.TimeoutExpired:
        print("[Premium subs] pycaps render timed out.")
        return None
    return out_abs if os.path.isfile(out_abs) else None


def _pill_rgba_array(
    width: int,
    height: int,
    radius: int,
    fill: Tuple[int, int, int, int],
) -> Optional[np.ndarray]:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    width = max(2, width)
    height = max(2, height)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=fill)
    return np.array(img)


def _slide_position_fn(
    cy: int,
    clip_h: int,
    *,
    slide_px: int = 34,
    slide_sec: float = 0.16,
) -> Callable[[float], Tuple[str, int]]:
    """Top-left style position with horizontal centering; ease-up from below."""

    def pos(t: float) -> Tuple[str, int]:
        rel = min(1.0, max(0.0, t / slide_sec))
        ease = 1.0 - (1.0 - rel) ** 3
        off = int((1.0 - ease) * slide_px)
        return ("center", cy - clip_h // 2 + off)

    return pos


def apply_whisper_timed_subtitles_to_video(
    video_path: str,
    segments: List[Dict[str, Any]],
    output_path: str,
) -> Optional[str]:
    """
    Burn Whisper timings as premium captions: short phrases, frosted pill, fade + slide-in.
    """
    if not video_path or not os.path.isfile(video_path):
        print("[Premium subs] input video missing.")
        return None
    if not segments:
        print("[Premium subs] no segments to draw.")
        return None
    try:
        from moviepy import CompositeVideoClip, ImageClip, TextClip, VideoFileClip
        from moviepy.video.fx import FadeIn, FadeOut
    except ImportError as e:
        print(f"[Premium subs] moviepy required ({e}).")
        return None

    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    video = VideoFileClip(video_path)
    duration = max(float(video.duration or 0), 0.1)
    w, h = int(video.w), int(video.h)
    landscape = w >= h
    max_w = int(w * (0.82 if landscape else 0.88))
    font_size = max(22, int(h * (0.038 if landscape else 0.042)))
    stroke_w = max(2, int(font_size * 0.065))
    pad_x, pad_y = 22, 14
    radius = min(18, max(10, font_size // 2))
    cy = int(h * (0.745 if landscape else 0.66))

    clips: List[Any] = [video]
    try:
        for seg in segments:
            start = max(0.0, float(seg["start"]))
            end = min(duration, float(seg["end"]))
            if end - start < 0.06:
                continue
            raw = (seg.get("text") or "").strip()
            if not raw:
                continue
            width_chars = max(10, max_w // max(7, int(font_size * 0.52)))
            lines = textwrap.wrap(raw, width=width_chars)
            body = "\n".join(lines) if lines else raw
            dur = end - start
            tc = TextClip(
                text=body,
                font_size=font_size,
                color="#F5F5F5",
                stroke_color="#050508",
                stroke_width=stroke_w,
                method="caption",
                size=(max_w, None),
            )
            tw, th = (int(tc.w), int(tc.h))
            pill_w = tw + 2 * pad_x
            pill_h = th + 2 * pad_y
            pill_arr = _pill_rgba_array(
                pill_w,
                pill_h,
                radius,
                (18, 20, 28, 238),
            )
            fi = min(0.13, dur * 0.35)
            fo = min(0.12, dur * 0.3)
            if fi + fo > dur * 0.85:
                fi = fo = max(0.04, dur * 0.22)

            text_fx = [FadeIn(fi), FadeOut(fo)]
            # RGBA pill: fade from/to transparent so the panel doesn’t flash black.
            pill_fx = [
                FadeIn(fi, initial_color=[0, 0, 0, 0]),
                FadeOut(fo, final_color=[0, 0, 0, 0]),
            ]

            if pill_arr is not None:
                bg = (
                    ImageClip(pill_arr)
                    .with_duration(dur)
                    .with_start(start)
                    .with_position(_slide_position_fn(cy, pill_h))
                    .with_effects(pill_fx)
                )
                clips.append(bg)

            tc = (
                tc.with_duration(dur)
                .with_start(start)
                .with_position(_slide_position_fn(cy, th))
                .with_effects(text_fx)
            )
            clips.append(tc)

        final = CompositeVideoClip(clips).with_duration(duration)
        final.audio = video.audio
        write_kw: Dict[str, Any] = {
            "codec": "libx264",
            "temp_audiofile": "temp-premium-subs-audio.m4a",
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
        for c in clips[1:]:
            try:
                c.close()
            except Exception:
                pass
        return out_abs if os.path.isfile(out_abs) else None
    except Exception as e:
        print(f"[Premium subs] render failed: {e}")
        try:
            video.close()
        except Exception:
            pass
    return None


def apply_premium_voice_and_subtitles(
    video_mp4: str,
    subtitle_text: str,
    output_mp4: str,
    *,
    burn_whisper_subtitles: bool = True,
    kokoro_voice: Optional[str] = None,
    whisper_model: Optional[str] = None,
    kokoro_speed: float = 1.0,
    subtitle_engine: str = "moviepy",
    pycaps_template: str = "dynamic-neon-pop",
    pycaps_video_quality: str = "very_high",
    pycaps_layout_align: str = "bottom",
    pycaps_layout_offset: Optional[float] = 0.0,
    pycaps_preview: bool = False,
    fit_audio_to_video: bool = False,
    narration_wav_path: Optional[str] = None,
) -> Optional[str]:
    """
    Kokoro WAV → align timeline → mux → optional Whisper timed burn-in.

    By default (``fit_audio_to_video=False``) narration keeps natural speed; the video track is
    extended (last frame held) or trimmed so its duration matches the WAV. Whisper runs on that
    same audio for accurate captions.

    Set ``fit_audio_to_video=True`` to stretch/shrink speech to the current video length (legacy).

    Pass ``narration_wav_path`` to reuse an existing Kokoro render (skips synthesis and ignores
    empty ``subtitle_text`` for the TTS step).
    """
    tmp = tempfile.mkdtemp(prefix="premium_voice_")
    try:
        raw_wav: str
        if narration_wav_path:
            src = os.path.abspath(narration_wav_path)
            if not os.path.isfile(src):
                print("[Premium voice] narration_wav_path missing.")
                return None
            raw_wav = os.path.join(tmp, "kokoro_raw.wav")
            shutil.copy2(src, raw_wav)
        else:
            narr = narration_text_for_tts(subtitle_text)
            if not narr:
                print("[Premium voice] empty narration text.")
                return None
            raw_wav = os.path.join(tmp, "kokoro_raw.wav")
            if not synthesize_kokoro_wav(narr, raw_wav, voice=kokoro_voice, speed=kokoro_speed):
                return None

        fit_wav = os.path.join(tmp, "kokoro_fit.wav")
        muxed = os.path.join(tmp, "muxed.mp4")
        aligned_mp4 = os.path.join(tmp, "aligned.mp4")

        adur = _ffprobe_duration_seconds(raw_wav)
        if adur is None or adur <= 0:
            print("[Premium voice] could not read narration duration.")
            return None

        if fit_audio_to_video:
            vdur = _ffprobe_duration_seconds(video_mp4)
            if vdur is None:
                print("[Premium voice] could not read video duration.")
                return None
            if not fit_wav_to_duration_ffmpeg(raw_wav, fit_wav, vdur):
                print("[Premium voice] ffmpeg could not fit audio duration.")
                return None
            video_in = video_mp4
            audio_for_mux = fit_wav
            audio_for_whisper = fit_wav
        else:
            if not extend_or_trim_video_duration_ffmpeg(video_mp4, aligned_mp4, adur):
                print("[Premium voice] could not align video duration to narration.")
                return None
            video_in = aligned_mp4
            audio_for_mux = raw_wav
            audio_for_whisper = raw_wav

        out_mux = mux_video_and_wav(video_in, audio_for_mux, muxed)
        if not out_mux:
            return None
        current = out_mux
        whisper_hint = narration_text_for_tts(subtitle_text) if (subtitle_text or "").strip() else ""
        if burn_whisper_subtitles:
            engine = (subtitle_engine or "moviepy").strip().lower()
            if engine == "pycaps":
                raw = transcribe_whisper_full_result(
                    audio_for_whisper,
                    model_size=whisper_model,
                    initial_prompt=whisper_hint or None,
                )
                payload = whisper_raw_result_to_pycaps_whisper_json(raw) if raw else {}
                if not (payload.get("segments")):
                    print(
                        "[Premium voice] Whisper returned no usable segments for pycaps; "
                        "passing through muxed audio only."
                    )
                else:
                    wjson = os.path.join(tmp, "whisper_pycaps.json")
                    with open(wjson, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                    subbed = os.path.join(tmp, "pycaps_kinetic.mp4")
                    print(
                        f"[Premium subs] pycaps preset={pycaps_template!r} "
                        f"quality={pycaps_video_quality!r} (kinetic CSS subtitles)…"
                    )
                    done = run_pycaps_kinetic_render(
                        current,
                        wjson,
                        subbed,
                        template=pycaps_template,
                        video_quality=pycaps_video_quality,
                        layout_align=pycaps_layout_align,
                        layout_offset=pycaps_layout_offset,
                        preview=pycaps_preview,
                    )
                    if done:
                        current = done
            else:
                segs = transcribe_whisper_segments(
                    audio_for_whisper,
                    model_size=whisper_model,
                    initial_prompt=whisper_hint or None,
                )
                if not segs:
                    print("[Premium voice] Whisper returned no segments; passing through muxed audio only.")
                else:
                    subbed = os.path.join(tmp, "with_whisper_subs.mp4")
                    done = apply_whisper_timed_subtitles_to_video(current, segs, subbed)
                    if done:
                        current = done
        shutil.copy2(current, os.path.abspath(output_mp4))
        return os.path.abspath(output_mp4) if os.path.isfile(output_mp4) else None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

