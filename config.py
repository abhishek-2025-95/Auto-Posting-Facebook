# config.py - API Keys and Configuration
# Secrets are loaded from environment variables (use .env file with python-dotenv).
# Copy .env.example to .env and fill in your keys. Never commit .env or real keys.

import os

# Pipeline build id: printed at startup so you can verify RunPod is running the deployed code (e.g. in runpod.log)
PIPELINE_BUILD_ID = "no-magazine-headlines-v1"

# Load .env from same directory as this file (project root) so it works when run via nohup/SSH
_config_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_config_dir, ".env")
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
    # Optional: load a second env file (e.g. .env.india for India page) so overrides apply
    _env_extra = os.environ.get("ENV_FILE")
    if _env_extra:
        _extra_path = _env_extra if os.path.isabs(_env_extra) else os.path.join(_config_dir, _env_extra)
        load_dotenv(_extra_path)
except ImportError:
    pass

# Google AI Studio (Gemini) API Key (google-generativeai also checks GOOGLE_API_KEY)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
if GEMINI_API_KEY and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# News API Key (Using Newsdata.io) - https://newsdata.io/
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
# Reputed-source + recency: strict window first, then relaxed (still age-capped, newest-first). No stale unfiltered fallback.
NEWS_MAX_AGE_HOURS = float(os.environ.get("NEWS_MAX_AGE_HOURS", "8") or "8")
NEWS_RELAXED_MAX_AGE_HOURS = float(os.environ.get("NEWS_RELAXED_MAX_AGE_HOURS", "48") or "48")
# Wikipedia + light web snippets to enrich scene teaching points and Cursor image prompts (see news_research_brief.py).
_env_research = os.environ.get("ENABLE_NEWS_SECONDARY_RESEARCH", "1").strip().lower()
ENABLE_NEWS_SECONDARY_RESEARCH = _env_research not in ("0", "false", "no", "off")
NEWS_RESEARCH_TIMEOUT = float(os.environ.get("NEWS_RESEARCH_TIMEOUT", "12") or "12")
# Grow video narration (title/summary + research bullets + bridge lines) toward per-story ideal length.
_env_expand = os.environ.get("AUTO_EXPAND_VIDEO_NARRATION", "1").strip().lower()
AUTO_EXPAND_VIDEO_NARRATION = _env_expand not in ("0", "false", "no", "off")

# Facebook Graph API Configuration (use Page Access Token per page)
# Supports both FACEBOOK_* and PAGE_* env names (e.g. in .env: PAGE_ACCESS_TOKEN=..., PAGE_ID=...)
FACEBOOK_ACCESS_TOKEN = os.environ.get("FACEBOOK_ACCESS_TOKEN") or os.environ.get("PAGE_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID") or os.environ.get("PAGE_ID", "")
# Optional: for scripts/check_page_token_comments.py — debug_token needs app credentials (never commit secrets)
FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID", "").strip()
FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "").strip()

# Google Cloud Platform Configuration for Vertex AI (Imagen)
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "YOUR_GCP_PROJECT_ID_HERE")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

# Note: google-cloud-aiplatform (Vertex AI) requires authentication via a JSON service account
# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account JSON file
# Example: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# News API Configuration (Newsdata.io) – US, UK & Europe for enormous pipeline
NEWS_LANGUAGE = os.environ.get("NEWS_LANGUAGE", "en")
# When True: only US + European economy / financial-markets–relevant stories (filters + business RSS/Reddit/Google bias).
# Default ON — page focuses on financial markets & economy only (not sports/entertainment/general).
# Set NEWS_MARKETS_US_EUROPE_ONLY=0 to widen to general breaking news (not recommended for a markets page).
_mkt_only = os.environ.get("NEWS_MARKETS_US_EUROPE_ONLY", "true").strip().lower()
NEWS_MARKETS_US_EUROPE_ONLY = _mkt_only not in ("0", "false", "no", "off")
# Newsdata.io category (e.g. business) when markets focus is on; empty = no category filter
_env_nd_cat = os.environ.get("NEWSDATA_CATEGORY", "").strip()
if _env_nd_cat:
    NEWSDATA_CATEGORY = _env_nd_cat
elif NEWS_MARKETS_US_EUROPE_ONLY:
    NEWSDATA_CATEGORY = "business"
else:
    NEWSDATA_CATEGORY = ""
# Countries to fetch (comma-separated in env NEWS_COUNTRIES overrides this list). For India-only page use NEWS_COUNTRIES=in
_env_countries = os.environ.get("NEWS_COUNTRIES", "").strip()
_NEWS_COUNTRIES_US_EU = [
    "us", "gb", "de", "fr", "it", "es", "nl", "ie", "be", "at", "pl", "pt", "ch", "se", "no", "dk", "fi",
]
_NEWS_COUNTRIES_GENERAL = [
    "us", "gb", "de", "fr", "it", "es", "nl", "ie", "be", "at", "pl", "pt", "ch", "se",
]
if _env_countries:
    NEWS_COUNTRIES = [c.strip().lower() for c in _env_countries.split(",") if c.strip()]
elif NEWS_MARKETS_US_EUROPE_ONLY:
    NEWS_COUNTRIES = list(_NEWS_COUNTRIES_US_EU)
else:
    NEWS_COUNTRIES = list(_NEWS_COUNTRIES_GENERAL)

# Breaking financial markets + economy (US/Europe) from reputable outlets only — no Reddit/Google aggregators.
# Default ON. Set NEWS_BREAKING_FINANCE_REPUTED_ONLY=0 to allow broader sources (not recommended).
_env_bfr = os.environ.get("NEWS_BREAKING_FINANCE_REPUTED_ONLY", "true").strip().lower()
NEWS_BREAKING_FINANCE_REPUTED_ONLY = _env_bfr not in ("0", "false", "no", "off")
_env_brh = os.environ.get("NEWS_REQUIRE_BREAKING_HEADLINE", "true").strip().lower()
NEWS_REQUIRE_BREAKING_HEADLINE = _env_brh not in ("0", "false", "no", "off")
# When True (default): only **premier** business outlets pass ``_source_is_reputed_finance_outlet``
# (wires + major WSJ/FT/CNBC-tier sources). Set NEWS_REPUTED_PREMIER_ONLY=0 to also allow secondary names
# (Yahoo Finance, Seeking Alpha, Business Insider, etc.).
_env_rep_prem = os.environ.get("NEWS_REPUTED_PREMIER_ONLY", "true").strip().lower()
NEWS_REPUTED_PREMIER_ONLY = _env_rep_prem not in ("0", "false", "no", "off")

# Optional: page theme for captions – when markets focus and unset, default to US/EU markets theme
TOPIC_THEME = os.environ.get("TOPIC_THEME", "").strip() or None
if TOPIC_THEME is None and NEWS_BREAKING_FINANCE_REPUTED_ONLY:
    TOPIC_THEME = (
        "ONLY United States and European financial markets and economy news from reputable outlets "
        "(e.g. Reuters, Bloomberg, BBC Business, CNBC, Wall Street Journal, Financial Times). "
        "Do not cover sports, entertainment, celebrity, or general politics unless it directly moves markets "
        "(rates, regulation, trade, sanctions). Focus: stocks, bonds, FX, central banks, inflation, jobs, GDP, earnings, M&A."
    )
elif TOPIC_THEME is None and NEWS_MARKETS_US_EUROPE_ONLY:
    TOPIC_THEME = (
        "United States and European financial markets, economy, central banks, business, "
        "corporate earnings, stocks, bonds, inflation, trade, and macroeconomic policy"
    )
NEWS_HOURS_BACK = 24  # Look for news from last 24 hours (more articles)
NEWS_MAX_COUNTRIES = 14   # Max countries to query per fetch (use first N from NEWS_COUNTRIES)
NEWS_MAX_ARTICLES_PER_COUNTRY = 20  # Articles to request per country (larger pipeline)
NEWS_POOL_SIZE = 40  # Total articles to keep in merged pool for selection

# Posting Schedule Configuration
POSTS_PER_DAY = 10
MINUTES_BETWEEN_POSTS = 144  # 24 hours / 10 posts = 2.4 hours = 144 minutes
# Continuous 24x7 mode: seconds to wait between cycles when starting the next (avoids tight loop on no news/fail).
CONTINUOUS_POST_COOLDOWN_SECONDS = 30
# run_continuous_posts: US/Eastern windows (7–9am, 12–1pm, 7–10pm) + POSTS_PER_DAY cap.
# Default: evenly spaced slot times inside each window (no flood). Flood is opt-in: POSTING_SCHEDULE_SLOTS_ONLY=0 + POSTING_SCHEDULE_FLOOD_WINDOWS.
# Set ENABLE_US_ET_POSTING_WINDOWS=0 for old 24/7 behavior. Requires `tzdata` on some Windows installs for zoneinfo.
_et_sched = os.environ.get("ENABLE_US_ET_POSTING_WINDOWS", "1").strip().lower()
ENABLE_US_ET_POSTING_WINDOWS = _et_sched not in ("0", "false", "no", "off")
# When True: first ``run_continuous_image_posts.py`` cycle skips ``wait_until_allowed_post_slot`` (post one now),
# then later cycles use normal US/ET slot discipline. Set by run_fb_cursor_image_autostart.cmd / Task Scheduler.
_skip_first_et = os.environ.get("SKIP_US_ET_WAIT_FIRST_IMAGE_POST", "").strip().lower()
SKIP_US_ET_WAIT_FIRST_IMAGE_POST = _skip_first_et in ("1", "true", "yes", "on")

# IANA timezone for posting windows + daily cap.
# Default US Eastern: **America/New_York** (correct EST *and* EDT / daylight saving — prefer this over a fixed "EST" offset).
# Same clock windows in that zone: 7–9, 12–13, 19–22. Optional: IST/Asia/Kolkata only if you want those hours on **India** local time.
_raw_post_tz = os.environ.get("POSTING_SCHEDULE_TIMEZONE", "America/New_York").strip()
_POSTING_TZ_ALIASES = {
    "ist": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "asia/kolkata": "Asia/Kolkata",
    "et": "America/New_York",
    "est": "America/New_York",
    "edt": "America/New_York",
    "eastern": "America/New_York",
    "us/eastern": "America/New_York",
    "us_et": "America/New_York",
    "us_east": "America/New_York",
}
POSTING_SCHEDULE_TIMEZONE = _POSTING_TZ_ALIASES.get(_raw_post_tz.lower(), _raw_post_tz)

# When True (default): use evenly spaced **slot** times only — **flood** modes are ignored.
# Set POSTING_SCHEDULE_SLOTS_ONLY=0 in .env only if you intentionally want POSTING_SCHEDULE_FLOOD_WINDOWS.
_slots_only = os.environ.get("POSTING_SCHEDULE_SLOTS_ONLY", "true").strip().lower()
POSTING_SCHEDULE_SLOTS_ONLY = _slots_only not in ("0", "false", "no", "off")

# Image Generation Configuration (vertical feed stills: **4:5** portrait; override with IMAGE_ASPECT_RATIO in .env)
IMAGE_ASPECT_RATIO = os.environ.get("IMAGE_ASPECT_RATIO", "4:5").strip() or "4:5"
IMAGE_QUALITY = "high"
# Post stills: Cursor image tool only (see IMAGE_GENERATION_MODE below). Z-Image env below is unused for Facebook photo posts.
USE_ONLY_IMGEN_FEB = True
USE_IMGEN_FEB = True
USE_ONLY_LOCAL_IMAGE_MODEL = True
# PIL/text placeholder images: **permanently disabled** — Facebook post stills use the Cursor chat image tool only.
# .env cannot enable this; there is no scripted diffusion or PIL substitute for post art.
ALLOW_FALLBACK_POST_IMAGE = False
# Strict pipeline: fail fast on bad CUDA + optional Z-Image warm load (run_continuous_posts).
# Default off when unset; run_local.cmd / run_continuous_*_helper.cmd set STRICT_IMAGE_GEN=1.
_strict_ig = os.environ.get("STRICT_IMAGE_GEN", "false").strip().lower()
STRICT_IMAGE_GEN = _strict_ig in ("1", "true", "yes", "on")
_warm_default = "true" if STRICT_IMAGE_GEN else "false"
_warm_ig = os.environ.get("IMAGE_GEN_WARM_LOAD", _warm_default).strip().lower()
IMAGE_GEN_WARM_LOAD = _warm_ig not in ("0", "false", "no", "off")
# Pin Windows loader defaults when strict (override with env if needed)
if STRICT_IMAGE_GEN:
    os.environ.setdefault("HF_DEACTIVATE_ASYNC_LOAD", "1")
    if os.name == "nt":
        os.environ.setdefault("IMGEN_SAFE_SAFETENSORS_MODE", "clone")
# GPU + CPU combination for 24/7: use GPU with CPU offload, clear pipeline after each run to avoid VRAM buildup.
# Set IMGEN_FEB_DEVICE=cpu in .env to avoid local CUDA errors (e.g. illegal instruction / driver mismatch).
IMGEN_FEB_DEVICE = os.environ.get("IMGEN_FEB_DEVICE", "cuda").strip().lower()
# imgen feb generate_image.py reads IMGEN_DEVICE at import — must match FEB device so Windows safetensors mmap patch is skipped on CUDA (fast loads, no misleading "Windows+CPU" log).
os.environ.setdefault("IMGEN_DEVICE", IMGEN_FEB_DEVICE)
# CUDA defaults: offload-first (stable on ~12GB VRAM; full-GPU often crashes after shard load). Speed: IMGEN_TRY_DIRECT_GPU_FIRST=1 in .env
if IMGEN_FEB_DEVICE == "cuda":
    os.environ.setdefault("IMGEN_TRY_DIRECT_GPU_FIRST", "0")
    # GPU + CPU hybrid defaults (performance + memory efficiency):
    # - default: try CPU offload path first (IMGEN_TRY_DIRECT_GPU_FIRST=0)
    # - set IMGEN_TRY_DIRECT_GPU_FIRST=1 for full-GPU first if you have headroom
    if os.name == "nt":
        # Default OFF: full-GPU preload on Windows often native-crashes after shard load (RTX 40/50 + drivers).
        # Opt in: IMGEN_ALLOW_WINDOWS_DIRECT_GPU=1 together with IMGEN_TRY_DIRECT_GPU_FIRST=1
        os.environ.setdefault("IMGEN_ALLOW_WINDOWS_DIRECT_GPU", "0")
    os.environ.setdefault("IMGEN_OFFLOAD_VRAM_THRESHOLD_GB", "14")
    # expandable_segments is not supported on Windows PyTorch (warning + odd allocator behavior)
    if os.name != "nt":
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("USE_TORCH", "1")
    os.environ.setdefault("USE_TF", "0")

# Windows + CUDA: **override .env** — setdefault above cannot fix recurring STRATEGY-1 crashes when .env sets TRY_DIRECT=1.
# Opt out of this policy only with IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1 (expert / large VRAM only).
if os.name == "nt" and IMGEN_FEB_DEVICE == "cuda":
    _win_unsafe = os.environ.get("IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not _win_unsafe:
        os.environ["IMGEN_TRY_DIRECT_GPU_FIRST"] = "0"
        os.environ["IMGEN_ALLOW_WINDOWS_DIRECT_GPU"] = "0"
        # Model CPU offload: avoids native exit after checkpoint shards on ~12GB (OOM handler never runs).
        _no_force = os.environ.get("IMGEN_WIN_SKIP_FORCE_CPU_OFFLOAD", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if not _no_force:
            os.environ["IMGEN_FORCE_CPU_OFFLOAD"] = "1"
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    # User .env may still set expandable_segments — not supported on Windows torch (noisy + unhelpful)
    _pac = (os.environ.get("PYTORCH_CUDA_ALLOC_CONF") or "").lower()
    if "expandable_segments" in _pac:
        os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)

# CPU offload: when true, imgen_feb uses auto mode (None): direct GPU if VRAM >= IMGEN_OFFLOAD_VRAM_THRESHOLD_GB else model offload.
# Set IMGEN_FEB_USE_CPU_OFFLOAD=false to always force full-GPU load (fastest if it fits). IMGEN_FORCE_CPU_OFFLOAD=1 always offloads.
# IMGEN_TRY_DIRECT_GPU_FIRST=1 tries full-GPU first then OOM-fallback (good ~12GB + 32GB RAM). See PERFORMANCE.md.
_offload_default = "true"
_env_offload = os.environ.get("IMGEN_FEB_USE_CPU_OFFLOAD", _offload_default).strip().lower()
IMGEN_FEB_USE_CPU_OFFLOAD = _env_offload in ("1", "true", "yes", "")
# Even lower peak VRAM (slower): set IMGEN_SEQUENTIAL_CPU_OFFLOAD=1 in .env; imgen_feb uses sequential CPU offload.
# If IMGEN_FEB_DEVICE=cuda but PyTorch was installed without CUDA, we normally fall back to CPU (slow).
# Set IMGEN_ALLOW_CPU_FALLBACK=false to stop the pipeline from using CPU and print install steps instead.
_av_fb = os.environ.get("IMGEN_ALLOW_CPU_FALLBACK", "true").strip().lower()
IMGEN_ALLOW_CPU_FALLBACK = _av_fb in ("1", "true", "yes", "")
# New GPUs (e.g. RTX 50 / sm_100+): imgen_feb may force CPU unless you install a PyTorch build that supports your arch.
# Legacy flag (still in .env templates). imgen feb uses torch_cuda_compat — real matmul probe for sm_91+; not bypassed by this.
_skip_gpu = os.environ.get("IMGEN_SKIP_GPU_CAPABILITY_CHECK", "").strip().lower()
IMGEN_SKIP_GPU_CAPABILITY_CHECK = _skip_gpu in ("1", "true", "yes", "on")
# Clear pipeline after each image (True = free RAM/VRAM after each run; False = keep model loaded, faster next image).
# Default: True on CPU (large models + 32GB RAM), False on CUDA. Override with IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE=true|false
_env_clear = os.environ.get("IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE", "").strip().lower()
if _env_clear in ("1", "true", "yes"):
    IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE = True
elif _env_clear in ("0", "false", "no"):
    IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE = False
else:
    IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE = IMGEN_FEB_DEVICE == "cpu"
# Image size for imgen_feb: canvas width (height = width * 5/4 for **4:5** portrait). Smaller = less RAM on CPU.
# Default 768 on CPU, 1024 on GPU unless IMGEN_FEB_SIZE is set in .env
_env_size = os.environ.get("IMGEN_FEB_SIZE", "").strip()
if _env_size:
    try:
        IMGEN_FEB_SIZE = int(_env_size)
    except ValueError:
        IMGEN_FEB_SIZE = 1024
else:
    IMGEN_FEB_SIZE = 768 if IMGEN_FEB_DEVICE == "cpu" else 1024
# Z-Image-Turbo steps. CPU: 8; CUDA default 6 (faster, still good for Turbo). Override: IMGEN_FEB_INFERENCE_STEPS=8
_env_steps = os.environ.get("IMGEN_FEB_INFERENCE_STEPS", "").strip()
if _env_steps:
    try:
        IMGEN_FEB_INFERENCE_STEPS = max(1, min(50, int(_env_steps)))
    except ValueError:
        IMGEN_FEB_INFERENCE_STEPS = 8 if IMGEN_FEB_DEVICE == "cpu" else 6
else:
    IMGEN_FEB_INFERENCE_STEPS = 8 if IMGEN_FEB_DEVICE == "cpu" else 6


def get_post_image_dimensions_45():
    """
    (width, height) for vertical **4:5** portrait stills (Facebook/IG-style tall post).
    ``IMGEN_FEB_SIZE`` = width; height ≈ width * 5/4. Snapped to multiples of 8 for diffusers.
    """
    w = int(IMGEN_FEB_SIZE)
    w = max(256, (w // 8) * 8)
    h = int(round(w * 5.0 / 4.0))
    h = max(320, (h // 8) * 8)
    return w, h


# Run caption and prompt one after the other (True) to avoid burdening CPU/RAM before image gen; False = parallel (faster cycle, more load).
RUN_CAPTION_PROMPT_SEQUENTIAL = True
# Image generation model: Z-Image-Turbo (diffusers on RunPod / imgen_feb locally). Default: Tongyi-MAI/Z-Image-Turbo.
# Override in .env: Z_IMAGE_TURBO_MODEL=... (e.g. aiorbust/z-image-turbo if you have access).
Z_IMAGE_TURBO_MODEL = os.environ.get("Z_IMAGE_TURBO_MODEL", "Tongyi-MAI/Z-Image-Turbo")
# When True (default): image generation uses **only** ``runpod_image.py`` (Hugging Face diffusers Z-Image-Turbo).
# No ``imgen_feb`` package path and no secondary backend if diffusers fails.
_z_loc_only = os.environ.get("Z_IMAGE_LOCAL_DIFFUSERS_ONLY", "true").strip().lower()
Z_IMAGE_LOCAL_DIFFUSERS_ONLY = _z_loc_only not in ("0", "false", "no", "off")
# Append article summary beats into the diffusion prompt so the still reflects the full story (on-image depiction).
_cnews = os.environ.get("COMPREHENSIVE_NEWS_IMAGE_PROMPT", "true").strip().lower()
COMPREHENSIVE_NEWS_IMAGE_PROMPT = _cnews not in ("0", "false", "no", "off")
# Image source for Facebook **photo** pipeline: **locked** to Cursor chat image tool only.
# ``IMAGE_GENERATION_MODE`` in .env is ignored for post images — no local Z-Image / diffusers / API image gen for posts.
IMAGE_GENERATION_MODE = "cursor_only"
CURSOR_POST_IMAGE_INBOUND = os.environ.get("CURSOR_POST_IMAGE_INBOUND", "").strip() or os.path.join(
    _config_dir,
    "cursor_post_image.png",
)
CURSOR_POST_IMAGE_PROMPT_PATH = os.environ.get("CURSOR_POST_IMAGE_PROMPT_PATH", "").strip() or os.path.join(
    _config_dir,
    "CURSOR_POST_IMAGE_PROMPT.txt",
)
_consume_ci = os.environ.get("CURSOR_POST_IMAGE_CONSUME", "true").strip().lower()
CURSOR_POST_IMAGE_CONSUME = _consume_ci not in ("0", "false", "no", "off")
# cursor_only: after writing CURSOR_POST_IMAGE_PROMPT.txt, poll for inbound image up to this many seconds (0 = fail immediately if missing).
_cur_wait = os.environ.get("CURSOR_INBOUND_MAX_WAIT_SECONDS", "0").strip()
try:
    CURSOR_INBOUND_MAX_WAIT_SECONDS = max(0.0, float(_cur_wait))
except ValueError:
    CURSOR_INBOUND_MAX_WAIT_SECONDS = 0.0
_cur_poll = os.environ.get("CURSOR_INBOUND_POLL_INTERVAL_SECONDS", "2").strip()
try:
    CURSOR_INBOUND_POLL_INTERVAL_SECONDS = max(0.5, float(_cur_poll))
except ValueError:
    CURSOR_INBOUND_POLL_INTERVAL_SECONDS = 2.0
# Optional: run once after the prompt file is written (e.g. play sound, toast script). No image fallback — side-channel only.
CURSOR_PROMPT_READY_NOTIFY_CMD = os.environ.get("CURSOR_PROMPT_READY_NOTIFY_CMD", "").strip()
# Cursor Background Agents API (optional — see scripts/cursor_inbound_auto_bridge.py). Key: Cursor Dashboard → Integrations.
CURSOR_API_KEY = os.environ.get("CURSOR_API_KEY", "").strip()
CURSOR_BACKGROUND_AGENT_REPO = os.environ.get("CURSOR_BACKGROUND_AGENT_REPO", "").strip()
# Unset → "main". Explicit empty string in .env → omit ``ref`` in Background Agents API (use GitHub default branch).
_raw_bg_ref = os.environ.get("CURSOR_BACKGROUND_AGENT_REF")
if _raw_bg_ref is None:
    CURSOR_BACKGROUND_AGENT_REF = "main"
else:
    CURSOR_BACKGROUND_AGENT_REF = _raw_bg_ref.strip()
_bga = os.environ.get("CURSOR_BACKGROUND_AGENT_AUTO", "").strip().lower()
CURSOR_BACKGROUND_AGENT_AUTO = _bga in ("1", "true", "yes", "on")
# In-image headline safe zone for Cursor image tool prompts: symmetric horizontal inset as % of frame width (5–15).
# Default 12 — models often ignore part of the margin; higher values reduce edge clipping.
_cursor_inset = os.environ.get("CURSOR_HEADLINE_INSET_PCT", "12").strip()
try:
    CURSOR_HEADLINE_INSET_PCT = max(5, min(15, int(_cursor_inset)))
except ValueError:
    CURSOR_HEADLINE_INSET_PCT = 12
# cursor_only inbound normalization to target 4:5 (see get_post_image_dimensions_45):
# cover = scale + crop to FILL frame (default) — photo always full-bleed 4:5; may trim edges/headline if source isn’t 4:5.
# letterbox = scale to fit inside frame — no crop, but non-4:5 sources show bands (photo “isn’t” full 4:5 visually).
# headline_safe / center = crop-first paths (legacy / special cases).
_cic = os.environ.get("CURSOR_INBOUND_CROP_MODE", "cover").strip().lower()
CURSOR_INBOUND_CROP_MODE = (
    _cic if _cic in ("headline_safe", "center", "letterbox", "cover") else "cover"
)
# cursor_only: default **true** = typeset headline in minimal_overlay (fit/wrap to 4:5 — **headline stays inside frame**).
# Set false only if the Cursor image tool must paint the full chyron (often clips margins; use strict prompts + letterbox crop).
_cpil = os.environ.get("CURSOR_USE_PIL_HEADLINE_OVERLAY", "true").strip().lower()
CURSOR_USE_PIL_HEADLINE_OVERLAY = _cpil not in ("0", "false", "no", "off")
# When set, image generation is done on a remote RunPod server (only GPU part on RunPod; rest on VPS).
# Example: RUNPOD_IMAGE_API_URL=http://1.2.3.4:5000 (RunPod pod public IP and port of runpod_image_server.py).
RUNPOD_IMAGE_API_URL = os.environ.get("RUNPOD_IMAGE_API_URL", "")

# Image visual mode: "classic" = photoreal news photography (default for this page).
# "institutional" = dark terminal / abstract chart look (optional; set explicitly in .env).
# Do not use "market"/"markets" as aliases — avoids accidentally enabling chart mode on a markets-focused page.
_vm = os.environ.get("IMAGE_VISUAL_MODE", "classic").strip().lower()
IMAGE_VISUAL_MODE = (
    "institutional"
    if _vm in ("institutional", "institution", "terminal", "fintech")
    else "classic"
)
_accent_hex = os.environ.get("INSTITUTIONAL_ACCENT_HEX", "").strip()
if _accent_hex.startswith("#") and len(_accent_hex) == 7:
    INSTITUTIONAL_ACCENT_HEX = _accent_hex
else:
    INSTITUTIONAL_ACCENT_HEX = "#00B8D4"  # electric cyan-blue default for glow lines / overlay accent


def get_default_visual_style_for_image_prompt():
    """When IMAGE_VISUAL_MODE is institutional, return a style line for image prompts; else None."""
    if IMAGE_VISUAL_MODE == "institutional":
        return (
            "institutional dark-mode terminal; sleek minimalist charts; abstract structural shifts, "
            "break-of-structure and liquidity-sweep geometry (no readable labels); deep navy, slate, white; "
            f"sharp glowing accent {INSTITUTIONAL_ACCENT_HEX}; calculated professional edge—not retail noise; "
            "no photorealistic people or stock-photo tropes"
        )
    return None


# Sensational Breaking News template (4:5 vertical portrait when template is on)
USE_SENSATIONAL_BREAKING_TEMPLATE = os.environ.get("USE_SENSATIONAL_BREAKING_TEMPLATE", "true").strip().lower() in ("1", "true", "yes", "on")
SENSATIONAL_ASPECT_RATIO = os.environ.get("SENSATIONAL_ASPECT_RATIO", "4:5").strip() or "4:5"
# Minimal overlay: only "Breaking News" top-left + "AI Generated" bottom-right (no bar/headline/inset)
USE_MINIMAL_BREAKING_OVERLAY = os.environ.get("USE_MINIMAL_BREAKING_OVERLAY", "true").strip().lower() in ("1", "true", "yes", "on")

# Check Facebook page recent posts before posting to avoid duplicate news (same or very similar caption)
# Set CHECK_FACEBOOK_FOR_DUPLICATES=0 for a one-off test post (full workflow) when the picker keeps hitting a duplicate.
_env_fb_dup = os.environ.get("CHECK_FACEBOOK_FOR_DUPLICATES", "true").strip().lower()
CHECK_FACEBOOK_FOR_DUPLICATES = _env_fb_dup not in ("0", "false", "no", "off")
FACEBOOK_DUPLICATE_CHECK_LIMIT = 50   # Compare against last N posts
FACEBOOK_DUPLICATE_SIMILARITY = 0.65  # 0–1; if caption similarity >= this, skip post (0.65 = fairly similar)

# First comment on each post to boost engagement (algorithm tip: early comments increase reach)
ENABLE_FIRST_COMMENT = os.environ.get("ENABLE_FIRST_COMMENT", "true").lower() in ("1", "true", "yes")
FIRST_COMMENT_TEMPLATES = [
    "What do you think? Drop your take below 👇",
    "Tag someone who needs to see this 📌",
    "Follow for more breaking news 📰",
    "Share if this matters to you 🔄",
    "Comment below — we read every one 💬",
    "Read the full report here 👇",
]
# Article URL in the Page’s first comment (recommended for reach); set false to put URL back in main caption only
NEWS_LINK_IN_FIRST_COMMENT = os.environ.get("NEWS_LINK_IN_FIRST_COMMENT", "true").lower() in ("1", "true", "yes")
# When NEWS_LINK_IN_FIRST_COMMENT: add a short line on the post so people know to open the first comment
SHOW_FIRST_COMMENT_LINK_HINT = os.environ.get("SHOW_FIRST_COMMENT_LINK_HINT", "true").lower() in ("1", "true", "yes")

# Vintage Newspaper (Flodia-style) for Human Interest / long-form posts (2026 strategy)
USE_VINTAGE_NEWSPAPER_STYLE = False  # Original hyperrealistic image only (no newspaper overlay)

# Text (caption, image prompt, short headline): Ollama only. No Gemini; template fallback if Ollama fails.
USE_OLLAMA = os.environ.get("USE_OLLAMA", "true").lower() in ("1", "true", "yes")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")  # Ollama must be running (ollama serve)
OLLAMA_TEXT_MODEL = os.environ.get("OLLAMA_TEXT_MODEL", "llama3.2:3b")
OLLAMA_IMAGE_MODEL = os.environ.get("OLLAMA_IMAGE_MODEL", "x/z-image-turbo")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "600"))  # Seconds; increase when Ollama is shared by multiple projects
OLLAMA_RETRIES = int(os.environ.get("OLLAMA_RETRIES", "3"))  # Retries on timeout/busy (with backoff)
OLLAMA_RETRY_DELAY = int(os.environ.get("OLLAMA_RETRY_DELAY", "30"))  # Seconds to wait before first retry (backoff: 1x, 2x, 3x)
# Max tokens for caption generation (180–250 words need ~500–800 tokens). Set in .env as OLLAMA_CAPTION_NUM_PREDICT=1024
OLLAMA_CAPTION_NUM_PREDICT = int(os.environ.get("OLLAMA_CAPTION_NUM_PREDICT", "1024"))

# Remove any text drawn by the image model (OCR + inpainting) before overlay. Needs opencv + easyocr or pytesseract. Default on to avoid extra text in images.
REMOVE_TEXT_FROM_IMAGE = os.environ.get("REMOVE_TEXT_FROM_IMAGE", "true").lower() in ("1", "true", "yes")

# Manual Cursor video: Kokoro TTS + Whisper premium subtitles (premium_voice_subtitles.py)
KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "af_bella").strip() or "af_bella"
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small").strip() or "small"
