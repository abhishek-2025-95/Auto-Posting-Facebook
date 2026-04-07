"""Regression tests for branded video posting flow.

Run: python tests/test_branded_video_flow.py
"""
from __future__ import annotations

import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import content_generator as cg  # noqa: E402
import run_continuous_posts as rcp  # noqa: E402


def test_generate_post_video_uses_local_image_first_flow():
    article = {
        "title": "Fed signals caution as bond markets reprice rate path",
        "description": "Treasury yields and equities react after officials flag inflation persistence.",
    }
    with tempfile.TemporaryDirectory() as td:
        clip_path = os.path.join(td, "post_video.mp4")
        generated = {}

        old_generate_image = cg.generate_post_image_fallback
        old_clip = getattr(cg, "image_to_video_clip", None)

        def fake_generate_image(_article, image_prompt=None, output_path=None, system_prompt=None, topic_theme=None, visual_style=None):
            out = output_path or os.path.join(td, "post_image.jpg")
            with open(out, "wb") as f:
                f.write(b"fake-image")
            generated["image_path"] = out
            return out

        def fake_clip(image_file, output_path=None, duration_seconds=6, width=720, height=900, effect="zoom", fps=30):
            assert image_file == generated["image_path"]
            out = output_path or clip_path
            with open(out, "wb") as f:
                f.write(b"clip")
            generated["clip_path"] = out
            return out

        try:
            cg.generate_post_image_fallback = fake_generate_image
            cg.image_to_video_clip = fake_clip
            result = cg.generate_post_video(article)
            assert result == os.path.join(_ROOT, "post_video.mp4")
            assert os.path.exists(generated["clip_path"])
            assert not os.path.exists(generated["image_path"])
        finally:
            cg.generate_post_image_fallback = old_generate_image
            if old_clip is None:
                delattr(cg, "image_to_video_clip")
            else:
                cg.image_to_video_clip = old_clip


def test_run_image_cycle_posts_video_not_image():
    article = {
        "title": "Dollar jumps as traders digest central bank outlook",
        "description": "Markets rotate as policy expectations shift.",
        "url": "https://example.com/story",
    }
    with tempfile.TemporaryDirectory() as td:
        video_path = os.path.join(td, "post_video.mp4")
        posted = {}

        old_news = rcp.get_fresh_viral_news
        old_is_posted = rcp.is_article_posted
        old_caption = rcp.generate_facebook_caption
        old_video = getattr(rcp, "generate_post_video", None)
        old_duplicate = rcp.is_duplicate_on_facebook
        old_post = rcp.post_to_facebook_page
        old_comment = rcp.post_comment_on_post
        old_save = rcp.save_posted_article
        old_cleanup = rcp._memory_cleanup
        old_skip = rcp.SKIP_FACEBOOK_POST
        old_check_dup = rcp.CHECK_FACEBOOK_FOR_DUPLICATES
        old_sequential = rcp.RUN_CAPTION_PROMPT_SEQUENTIAL

        def fake_video(_article):
            with open(video_path, "wb") as f:
                f.write(b"video")
            return video_path

        try:
            rcp.get_fresh_viral_news = lambda: dict(article)
            rcp.is_article_posted = lambda _article: False
            rcp.generate_facebook_caption = lambda *_args, **_kwargs: "Caption body"
            rcp.generate_post_video = fake_video
            rcp.is_duplicate_on_facebook = lambda *_args, **_kwargs: False
            rcp.post_to_facebook_page = lambda caption, media_path, ai_label_already_applied=False: posted.update({
                "caption": caption,
                "media_path": media_path,
                "ai_label_already_applied": ai_label_already_applied,
            }) or "post123"
            rcp.post_comment_on_post = lambda *args, **kwargs: True
            rcp.save_posted_article = lambda _article: posted.update({"saved": True})
            rcp._memory_cleanup = lambda: None
            rcp.SKIP_FACEBOOK_POST = False
            rcp.CHECK_FACEBOOK_FOR_DUPLICATES = True
            rcp.RUN_CAPTION_PROMPT_SEQUENTIAL = True
            ok = rcp.run_image_cycle()
            assert ok is True
            assert posted["media_path"].endswith(".mp4")
            assert posted["ai_label_already_applied"] is False
        finally:
            rcp.get_fresh_viral_news = old_news
            rcp.is_article_posted = old_is_posted
            rcp.generate_facebook_caption = old_caption
            if old_video is None:
                delattr(rcp, "generate_post_video")
            else:
                rcp.generate_post_video = old_video
            rcp.is_duplicate_on_facebook = old_duplicate
            rcp.post_to_facebook_page = old_post
            rcp.post_comment_on_post = old_comment
            rcp.save_posted_article = old_save
            rcp._memory_cleanup = old_cleanup
            rcp.SKIP_FACEBOOK_POST = old_skip
            rcp.CHECK_FACEBOOK_FOR_DUPLICATES = old_check_dup
            rcp.RUN_CAPTION_PROMPT_SEQUENTIAL = old_sequential


def main() -> int:
    test_generate_post_video_uses_local_image_first_flow()
    test_run_image_cycle_posts_video_not_image()
    print("test_branded_video_flow: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
