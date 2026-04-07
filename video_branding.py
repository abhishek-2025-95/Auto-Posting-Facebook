"""Brand generated videos with breaking-news UI overlays."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Optional


def _get_font(size: int, weight: str = "bold"):
    try:
        from design_utils import get_font_by_weight

        return get_font_by_weight(size, weight, None)
    except Exception:
        from PIL import ImageFont

        return ImageFont.load_default()


def _build_overlay_frame(
    width: int,
    height: int,
    headline: Optional[str],
    *,
    show_headline_lower_third: bool = False,
    show_breaking_label: bool = False,
) -> "Image.Image":
    from PIL import Image, ImageDraw, ImageEnhance

    try:
        from design_config import (
            BREAKING_LABEL_TEXT,
            BREAKING_LABEL_HEIGHT_RATIO,
            BREAKING_LABEL_BG_RED,
            BREAKING_LABEL_BG_BLUE,
            BREAKING_LABEL_TEXT_COLOR,
            AI_LABEL_TEXT,
            AI_LABEL_TEXT_COLOR,
            UNSEEN_ECONOMY_LOGO_IMAGE_PATH,
            UNSEEN_ECONOMY_LOGO_TEXT,
            UNSEEN_ECONOMY_LOGO_COLOR,
            UNSEEN_ECONOMY_LOGO_BRIGHTNESS,
        )
    except Exception:
        BREAKING_LABEL_TEXT = "BREAKING NEWS"
        BREAKING_LABEL_HEIGHT_RATIO = 0.05
        BREAKING_LABEL_BG_RED = (220, 30, 45)
        BREAKING_LABEL_BG_BLUE = (30, 90, 220)
        BREAKING_LABEL_TEXT_COLOR = (255, 255, 255)
        AI_LABEL_TEXT = "AI Generated"
        AI_LABEL_TEXT_COLOR = (255, 255, 255)
        UNSEEN_ECONOMY_LOGO_IMAGE_PATH = None
        UNSEEN_ECONOMY_LOGO_TEXT = "The Unseen Economy"
        UNSEEN_ECONOMY_LOGO_COLOR = (255, 255, 255)
        UNSEEN_ECONOMY_LOGO_BRIGHTNESS = 1.85

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    short_side = min(width, height)

    # Breaking news banner (optional; off by default for cleaner frame + kinetic subs)
    if show_breaking_label:
        label_h = max(28, int(short_side * BREAKING_LABEL_HEIGHT_RATIO))
        label_font = _get_font(max(16, int(label_h * 0.45)), "bold")
        try:
            text_bbox = draw.textbbox((0, 0), BREAKING_LABEL_TEXT, font=label_font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
        except Exception:
            text_w = len(BREAKING_LABEL_TEXT) * max(10, int(label_h * 0.3))
            text_h = max(14, int(label_h * 0.4))
        pad_x = int(label_h * 0.55)
        pad_y = int(label_h * 0.35)
        label_w = text_w + 2 * pad_x
        x0 = max(12, int(width * 0.04))
        y0 = max(12, int(height * 0.04))
        x1 = x0 + label_w
        y1 = y0 + text_h + 2 * pad_y
        mid = x0 + (x1 - x0) // 2
        draw.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=BREAKING_LABEL_BG_RED)
        draw.rectangle([mid, y0, x1, y1], fill=BREAKING_LABEL_BG_BLUE)
        draw.text(
            (x0 + pad_x, y0 + pad_y),
            BREAKING_LABEL_TEXT,
            fill=BREAKING_LABEL_TEXT_COLOR,
            font=label_font,
        )

    # Optional lower-third headline bar (off by default — manual pipeline uses subtitles only)
    if show_headline_lower_third and headline:
        bar_h = max(72, int(height * 0.16))
        bar_y0 = height - bar_h - max(18, int(height * 0.06))
        draw.rounded_rectangle(
            [max(20, int(width * 0.05)), bar_y0, width - max(20, int(width * 0.05)), bar_y0 + bar_h],
            radius=18,
            fill=(12, 20, 64, 215),
        )
        head_font = _get_font(max(18, int(bar_h * 0.28)), "black")
        text = " ".join((headline or "").split()[:18]).strip() or "Breaking News"
        draw.text(
            (width // 2, bar_y0 + bar_h // 2),
            text,
            fill=(255, 255, 255),
            font=head_font,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )

    # AI label
    ai_font = _get_font(max(12, int(short_side * 0.018)), "regular")
    try:
        ai_bbox = draw.textbbox((0, 0), AI_LABEL_TEXT, font=ai_font)
        ai_w = ai_bbox[2] - ai_bbox[0]
        ai_h = ai_bbox[3] - ai_bbox[1]
    except Exception:
        ai_w = len(AI_LABEL_TEXT) * 8
        ai_h = 16
    ai_x = width - ai_w - max(8, int(width * 0.01))
    ai_y = height - ai_h - max(8, int(height * 0.01))
    draw.text((ai_x, ai_y), AI_LABEL_TEXT, fill=AI_LABEL_TEXT_COLOR, font=ai_font)

    # Logo — boosted brightness + contrast so it reads on dark / busy frames
    if UNSEEN_ECONOMY_LOGO_IMAGE_PATH and os.path.exists(UNSEEN_ECONOMY_LOGO_IMAGE_PATH):
        try:
            logo = Image.open(UNSEEN_ECONOMY_LOGO_IMAGE_PATH).convert("RGBA")
            max_h = max(30, int(height * 0.12))
            scale = min(1.0, max_h / logo.height)
            logo = logo.resize((max(1, int(logo.width * scale)), max(1, int(logo.height * scale))), Image.Resampling.LANCZOS)
            brightness = max(1.0, min(2.2, float(UNSEEN_ECONOMY_LOGO_BRIGHTNESS)))
            r, g, b, a = logo.split()
            logo = Image.merge(
                "RGBA",
                (
                    ImageEnhance.Brightness(r).enhance(brightness),
                    ImageEnhance.Brightness(g).enhance(brightness),
                    ImageEnhance.Brightness(b).enhance(brightness),
                    a,
                ),
            )
            rgb = logo.convert("RGB")
            rgb = ImageEnhance.Contrast(rgb).enhance(1.2)
            r2, g2, b2 = rgb.split()
            logo = Image.merge("RGBA", (r2, g2, b2, a))
            overlay.paste(logo, (width - logo.width - 12, 12), logo)
        except Exception:
            pass
    else:
        logo_font = _get_font(max(16, int(short_side * 0.032)), "bold")
        logo_text = UNSEEN_ECONOMY_LOGO_TEXT
        try:
            logo_bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
            logo_w = logo_bbox[2] - logo_bbox[0]
        except Exception:
            logo_w = len(logo_text) * 10
        lx, ly = width - logo_w - 14, 14
        draw.text(
            (lx, ly),
            logo_text,
            fill=UNSEEN_ECONOMY_LOGO_COLOR,
            font=logo_font,
            stroke_width=3,
            stroke_fill=(0, 0, 0),
        )

    return overlay


def brand_video_for_posting(
    video_path: str,
    headline: Optional[str] = None,
    output_path: Optional[str] = None,
    *,
    show_headline_lower_third: bool = False,
    show_breaking_label: bool = False,
) -> Optional[str]:
    """Overlay branding on a rendered MP4: AI label + logo by default; optional breaking pill + headline bar."""
    if not video_path or not os.path.exists(video_path):
        print("Video branding skipped: input video missing.")
        return None
    try:
        import numpy as np
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.video.VideoClip import ImageClip

        output_path = output_path or os.path.join(os.path.dirname(video_path), "post_video_branded.mp4")
        video = VideoFileClip(video_path)
        overlay = _build_overlay_frame(
            video.w,
            video.h,
            headline=headline,
            show_headline_lower_third=show_headline_lower_third,
            show_breaking_label=show_breaking_label,
        )
        overlay_clip = ImageClip(np.array(overlay), duration=video.duration).set_position((0, 0))
        final = CompositeVideoClip([video, overlay_clip])
        final.audio = video.audio
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-branded-audio.m4a",
            remove_temp=True,
            fps=max(24, int(round(video.fps or 24))),
            preset="medium",
            ffmpeg_params=["-crf", "18"],
            logger=None,
        )
        video.close()
        overlay_clip.close()
        final.close()
        print(f"Branded video saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"Video branding failed: {e}")
        return None


def composite_branding_on_image(
    image_path: str,
    output_path: str,
    *,
    width: int = 1920,
    height: int = 1080,
    headline: Optional[str] = None,
    show_breaking_label: bool = True,
    show_headline_lower_third: bool = False,
) -> Optional[str]:
    """
    Fit ``image_path`` to ``width``×``height`` and alpha-composite breaking label, AI label, and logo (same as video overlay).
    Saves PNG (RGB) for ffmpeg / uploads.
    """
    from PIL import Image, ImageOps

    if not image_path or not os.path.isfile(image_path):
        print("Thumbnail branding skipped: image missing.")
        return None
    try:
        base = Image.open(image_path).convert("RGBA")
        base = ImageOps.fit(base, (width, height), method=Image.Resampling.LANCZOS)
        overlay = _build_overlay_frame(
            width,
            height,
            headline,
            show_headline_lower_third=show_headline_lower_third,
            show_breaking_label=show_breaking_label,
        )
        out = Image.alpha_composite(base, overlay)
        out_abs = os.path.abspath(output_path)
        parent = os.path.dirname(out_abs)
        if parent:
            os.makedirs(parent, exist_ok=True)
        out.convert("RGB").save(out_abs, "PNG", optimize=True)
        print(f"Branded thumbnail saved: {out_abs}")
        return out_abs if os.path.isfile(out_abs) else None
    except Exception as e:
        print(f"Thumbnail branding failed: {e}")
        return None


def _ffprobe_audio_sample_rate(video_path: str) -> Optional[int]:
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate",
                "-of",
                "json",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout or "{}")
        streams = data.get("streams") or []
        if not streams:
            return None
        return int(float(streams[0]["sample_rate"]))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError):
        return None


def prepend_image_intro_to_video(
    intro_image_path: str,
    main_video_path: str,
    output_path: str,
    *,
    intro_seconds: float = 2.5,
    fps: int = 30,
) -> Optional[str]:
    """
    Prepend a silent-audio still ``intro_image_path`` clip before ``main_video_path`` (h264+aac out).
    """
    if not intro_image_path or not os.path.isfile(intro_image_path):
        print("Intro prepend skipped: intro image missing.")
        return None
    if not main_video_path or not os.path.isfile(main_video_path):
        print("Intro prepend skipped: main video missing.")
        return None
    sr = _ffprobe_audio_sample_rate(main_video_path) or 48000
    intro_seconds = max(0.5, min(15.0, float(intro_seconds)))
    tmp_intro = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_intro.close()
    intro_mp4 = tmp_intro.name
    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        cmd_intro = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            os.path.abspath(intro_image_path),
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=channel_layout=stereo:sample_rate={sr}",
            "-t",
            f"{intro_seconds:.3f}",
            "-r",
            str(int(fps)),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            intro_mp4,
        ]
        subprocess.run(cmd_intro, check=True, capture_output=True, timeout=300)
        if not os.path.isfile(intro_mp4):
            return None
        cmd_cat = [
            "ffmpeg",
            "-y",
            "-i",
            intro_mp4,
            "-i",
            os.path.abspath(main_video_path),
            "-filter_complex",
            "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            out_abs,
        ]
        subprocess.run(cmd_cat, check=True, capture_output=True, timeout=7200)
        return out_abs if os.path.isfile(out_abs) else None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        err = getattr(e, "stderr", None) or b""
        msg = err.decode(errors="replace") if isinstance(err, bytes) else str(e)
        print(f"Intro prepend failed: {msg[:500]}")
        return None
    finally:
        try:
            os.unlink(intro_mp4)
        except OSError:
            pass
