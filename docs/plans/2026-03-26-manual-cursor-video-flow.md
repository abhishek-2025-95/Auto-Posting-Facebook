# Manual Cursor Video Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a manual assisted video workflow that uses Cursor-generated images to render a branded 5-image, 18-second finance-news video with a single coherent story arc and full-summary subtitles.

**Architecture:** Keep scheduled automation separate. Add a manual pipeline that takes one selected finance story, generates five image prompts/scenes for Cursor image generation, assembles those images into one 18-second vertical MP4, and composites branding plus full-summary subtitles into the final render. Reuse the repo’s current news selection, caption generation, headline helpers, branding config, and Facebook posting support without breaking the existing image/video automation paths.

**Tech Stack:** Python, existing repo modules, ffmpeg / local clip generation, PIL branding assets, subtitle/video composition helpers already in repo, manual Cursor image generation outside Python runtime.

---

### Task 1: Add manual workflow data model

**Files:**
- Create: `manual_cursor_video_flow.py`
- Test: `tests/test_manual_cursor_video_flow.py`

**Step 1: Write the failing test**

```python
def test_build_story_arc_returns_five_scenes():
    article = {
        "title": "Fed warns inflation progress may stall",
        "description": "Markets turn volatile as bond yields rise and traders reprice rate cuts.",
    }
    arc = build_manual_video_story_arc(article)
    assert len(arc["scenes"]) == 5
    assert arc["duration_seconds"] == 18
    assert arc["subtitle_text"]
```

**Step 2: Run test to verify it fails**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: FAIL because `build_manual_video_story_arc` does not exist yet.

**Step 3: Write minimal implementation**

```python
def build_manual_video_story_arc(article):
    return {
        "duration_seconds": 18,
        "scene_count": 5,
        "scenes": [... five scene dicts ...],
        "subtitle_text": full_summary,
    }
```

**Step 4: Run test to verify it passes**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: PASS

### Task 2: Add prompt pack generator for Cursor images

**Files:**
- Modify: `manual_cursor_video_flow.py`
- Test: `tests/test_manual_cursor_video_flow.py`

**Step 1: Write the failing test**

```python
def test_scene_prompts_keep_one_coherent_story_arc():
    pack = build_manual_video_story_arc(article)
    prompts = build_cursor_prompt_pack(pack)
    assert len(prompts) == 5
    assert all("same event" in p["continuity_notes"].lower() for p in prompts)
```

**Step 2: Run test to verify it fails**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: FAIL because `build_cursor_prompt_pack` is missing.

**Step 3: Write minimal implementation**

```python
def build_cursor_prompt_pack(story_pack):
    # scene 1 hook, scene 2 context, scene 3 impact, scene 4 reaction, scene 5 resolution
    ...
```

**Step 4: Run test to verify it passes**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: PASS

### Task 3: Add local render from five supplied images

**Files:**
- Modify: `manual_cursor_video_flow.py`
- Create: `scripts/render_manual_cursor_video.py`
- Test: `tests/test_manual_cursor_video_flow.py`

**Step 1: Write the failing test**

```python
def test_render_manifest_requires_five_images():
    with pytest.raises(ValueError):
        render_manual_cursor_video(["a.png", "b.png"])
```

**Step 2: Run test to verify it fails**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: FAIL because renderer is missing.

**Step 3: Write minimal implementation**

```python
def render_manual_cursor_video(image_paths, subtitle_text, headline, output_path):
    # validate 5 images
    # assign ~3.6s per scene
    # stitch scenes into 9:16 MP4
    # return output_path
```

**Step 4: Run test to verify it passes**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: PASS

### Task 4: Add branding and complete-summary subtitles

**Files:**
- Modify: `manual_cursor_video_flow.py`
- Reuse: `design_config.py`, `video_branding.py` or shared branding helpers
- Test: `tests/test_manual_cursor_video_flow.py`

**Step 1: Write the failing test**

```python
def test_render_plan_includes_breaking_ai_logo_and_full_summary():
    plan = build_render_plan(article)
    assert plan["branding"]["breaking_news"] is True
    assert plan["branding"]["ai_generated"] is True
    assert plan["branding"]["unseen_economy_logo"] is True
    assert plan["subtitles_mode"] == "full_summary"
```

**Step 2: Run test to verify it fails**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: FAIL until branding/subtitle plan is added.

**Step 3: Write minimal implementation**

```python
def build_render_plan(article):
    return {
        "branding": {...},
        "subtitles_mode": "full_summary",
    }
```

**Step 4: Run test to verify it passes**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: PASS

### Task 5: Add manual operator entrypoint

**Files:**
- Create: `scripts/render_manual_cursor_video.py`
- Modify: `README.md`

**Step 1: Write the failing test**

```python
def test_cli_outputs_prompt_pack_paths(tmp_path):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: FAIL until CLI exists.

**Step 3: Write minimal implementation**

```python
# phase A: build scene prompt pack + manifest for Cursor image generation
# phase B: accept five image paths and render final MP4
```

**Step 4: Run test to verify it passes**

Run: `python tests/test_manual_cursor_video_flow.py`

Expected: PASS

### Task 6: Verify end-to-end and document operator steps

**Files:**
- Modify: `README.md`
- Modify: `tests/test_manual_cursor_video_flow.py`

**Step 1: Verification commands**

Run:

```bash
python tests/test_manual_cursor_video_flow.py
python -m py_compile manual_cursor_video_flow.py scripts/render_manual_cursor_video.py
```

Expected: PASS / exit 0

**Step 2: Document operator flow**

Include:
- command to generate the 5-scene prompt pack
- where to drop the 5 Cursor-generated images
- command to render the final 18-second MP4
- output path of final video

**Step 3: Commit**

Only if explicitly requested by the user.
