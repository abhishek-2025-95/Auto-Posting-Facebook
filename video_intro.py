"""Prepend a static image as a timed intro clip to an MP4 (ffmpeg)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple


def _ffprobe_streams(path: str) -> Tuple[int, int, float, Optional[int], int]:
    """width, height, fps, audio_sample_rate (or None), max(audio_channels, 0)."""
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            path,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or "ffprobe failed")
    data = json.loads(r.stdout or "{}")
    streams: List[Dict[str, Any]] = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not v:
        raise RuntimeError("no video stream")
    w, h = int(v["width"]), int(v["height"])
    fps_s = v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1"
    if isinstance(fps_s, str) and "/" in fps_s:
        a, b = fps_s.split("/", 1)
        fps = float(a) / float(b) if float(b) else 30.0
    else:
        fps = float(fps_s) if fps_s else 30.0
    if fps < 1 or fps > 120:
        fps = 30.0
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not a:
        return w, h, fps, None, 0
    sr = int(a.get("sample_rate") or 48000)
    ch = int(a.get("channels") or 2)
    return w, h, fps, sr, ch


def prepend_png_intro_to_video(
    main_mp4: str,
    png_path: str,
    out_mp4: str,
    *,
    intro_seconds: float = 1.75,
) -> Optional[str]:
    """
    Prepend ``png_path`` as a still (``intro_seconds``) matching main video size, fps, and audio layout.
    Main video keeps its audio after a matching silent pad on the intro.
    """
    if not main_mp4 or not os.path.isfile(main_mp4):
        return None
    if not png_path or not os.path.isfile(png_path):
        return None
    intro_seconds = max(0.4, min(12.0, float(intro_seconds)))
    out_abs = os.path.abspath(out_mp4)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    try:
        w, h, fps, sr, ch = _ffprobe_streams(main_mp4)
    except Exception as e:
        print(f"[Thumb intro] probe failed: {e}")
        return None

    sr = sr or 48000
    has_audio = ch > 0
    ch = max(1, min(2, ch or 2))
    layout = "stereo" if ch >= 2 else "mono"
    tmpd = tempfile.mkdtemp(prefix="vid_intro_")
    try:
        intro_clip = os.path.join(tmpd, "intro.mp4")
        cmd_intro: List[str] = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(round(fps, 4)),
            "-i",
            os.path.abspath(png_path),
        ]
        if has_audio:
            cmd_intro += [
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=channel_layout={layout}:sample_rate={sr}",
            ]
        cmd_intro += [
            "-t",
            f"{intro_seconds:.4f}",
            "-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-r",
            str(round(fps, 4)),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
        if has_audio:
            cmd_intro += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        else:
            cmd_intro += ["-an"]
        cmd_intro.append(intro_clip)
        subprocess.run(cmd_intro, check=True, capture_output=True, timeout=300)

        lst = os.path.join(tmpd, "concat.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for p in (intro_clip, os.path.abspath(main_mp4)):
                posix = p.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{posix}'\n")

        cmd_cat = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            lst,
            "-c",
            "copy",
            out_abs,
        ]
        try:
            subprocess.run(cmd_cat, check=True, capture_output=True, timeout=600)
        except subprocess.CalledProcessError:
            cmd_re = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                lst,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                out_abs,
            ]
            subprocess.run(cmd_re, check=True, capture_output=True, timeout=900)

        return out_abs if os.path.isfile(out_abs) else None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        err = getattr(e, "stderr", None) or getattr(e, "stdout", None) or str(e)
        if isinstance(err, bytes):
            err = err.decode("utf-8", errors="replace")
        print(f"[Thumb intro] ffmpeg failed: {err[:800] if err else e}")
        return None
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
