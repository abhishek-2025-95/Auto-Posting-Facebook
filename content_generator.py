# content_generator.py - Captions (Ollama); Facebook post stills via Cursor image tool only (see config.IMAGE_GENERATION_MODE).
# Protobuf 5+: runtime_version must include Domain + ValidateProtobufRuntimeVersion (see protobuf_runtime_shim.py).
import protobuf_runtime_shim  # noqa: F401
# Workaround: broken/partial transformers installs omit top-level exports diffusers needs (AutoImageProcessor, PreTrainedModel, …)
try:
    import transformers_shim  # noqa: F401 — must run before diffusers
except Exception:
    pass

import json
import os
import re
import time
from datetime import datetime
from config import GCP_PROJECT_ID, GCP_LOCATION, IMAGE_ASPECT_RATIO
try:
    from config import USE_OLLAMA
except ImportError:
    USE_OLLAMA = False
try:
    from config import USE_ONLY_LOCAL_IMAGE_MODEL
except ImportError:
    USE_ONLY_LOCAL_IMAGE_MODEL = False
try:
    from config import USE_ONLY_IMGEN_FEB, USE_IMGEN_FEB
except ImportError:
    USE_ONLY_IMGEN_FEB = False
    USE_IMGEN_FEB = True
try:
    from config import (
        IMGEN_FEB_SIZE,
        IMGEN_FEB_DEVICE,
        IMGEN_FEB_USE_CPU_OFFLOAD,
        IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE,
        IMGEN_FEB_INFERENCE_STEPS,
        IMGEN_ALLOW_CPU_FALLBACK,
        RUNPOD_IMAGE_API_URL,
    )
except ImportError:
    IMGEN_FEB_SIZE = 1024
    IMGEN_FEB_DEVICE = "cuda"
    IMGEN_FEB_USE_CPU_OFFLOAD = True
    IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE = True
    IMGEN_FEB_INFERENCE_STEPS = 6
    IMGEN_ALLOW_CPU_FALLBACK = True
    RUNPOD_IMAGE_API_URL = ""
try:
    from config import get_post_image_dimensions_45, SENSATIONAL_ASPECT_RATIO
except ImportError:
    SENSATIONAL_ASPECT_RATIO = "4:5"

    def get_post_image_dimensions_45():
        w = int(IMGEN_FEB_SIZE)
        w = max(256, (w // 8) * 8)
        h = int(round(w * 5.0 / 4.0))
        h = max(320, (h // 8) * 8)
        return w, h


try:
    from config import USE_SENSATIONAL_BREAKING_TEMPLATE, USE_MINIMAL_BREAKING_OVERLAY
except ImportError:
    USE_SENSATIONAL_BREAKING_TEMPLATE = True   # default ON so overlay (Breaking News, logo, headline) is applied
    USE_MINIMAL_BREAKING_OVERLAY = True
    print("Warning: config.py not loaded for overlay flags; using defaults (overlay ON).")
try:
    from config import IMAGE_VISUAL_MODE, INSTITUTIONAL_ACCENT_HEX, get_default_visual_style_for_image_prompt
except ImportError:
    IMAGE_VISUAL_MODE = "classic"
    INSTITUTIONAL_ACCENT_HEX = "#00B8D4"

    def get_default_visual_style_for_image_prompt():
        return None
try:
    from config import Z_IMAGE_LOCAL_DIFFUSERS_ONLY, COMPREHENSIVE_NEWS_IMAGE_PROMPT
except ImportError:
    Z_IMAGE_LOCAL_DIFFUSERS_ONLY = False
    COMPREHENSIVE_NEWS_IMAGE_PROMPT = True
try:
    from config import (
        IMAGE_GENERATION_MODE,
        CURSOR_POST_IMAGE_INBOUND,
        CURSOR_POST_IMAGE_PROMPT_PATH,
        CURSOR_POST_IMAGE_CONSUME,
    )
except ImportError:
    IMAGE_GENERATION_MODE = "cursor_only"
    CURSOR_POST_IMAGE_INBOUND = ""
    CURSOR_POST_IMAGE_PROMPT_PATH = ""
    CURSOR_POST_IMAGE_CONSUME = True

# Vertex AI: optional; catch all errors (protobuf/grpc mismatches on system Python, etc.)
try:
    from google.cloud import aiplatform  # noqa: F401

    VERTEX_AI_AVAILABLE = True
except Exception:
    VERTEX_AI_AVAILABLE = False
    print("Vertex AI not available - will use Imagen 4")

# Try to import Imagen 4 (better option)
try:
    from google import genai as imagen_genai
    from google.genai import types
    IMAGEN_4_AVAILABLE = True
except ImportError:
    IMAGEN_4_AVAILABLE = False
    print("Imagen 4 not available - will use fallback")

# Try to import imgen_feb (Z-Image-Turbo). On a RunPod *pod* with RUNPOD=1, the same project uses runpod_image.py in-container.
try:
    import imgen_feb
    IMGEN_FEB_AVAILABLE = True
except ImportError:
    IMGEN_FEB_AVAILABLE = bool(os.environ.get("RUNPOD"))

# Gemini not used for main pipeline (caption/image prompt/headline use Ollama only). Lazy import only where still needed.
genai = None
def _genai():
    global genai
    if genai is None:
        import google.generativeai as _g
        genai = _g
        from config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
    return genai

# Post image path: always in project folder so file is easy to find and post step finds it
_CONTENT_GEN_BASE = os.path.dirname(os.path.abspath(__file__))
POST_IMAGE_PATH = os.path.join(_CONTENT_GEN_BASE, "post_image.jpg")

from ai_label import add_ai_generated_label  # Mandatory for all image posts

# Caption length: prompt asks for 180–250 words *before* hashtags. Models often return ~90–120 words of body
# plus many hashtags; old code accepted total word count ≥90 so posts looked "small" in the feed.
TARGET_CAPTION_BODY_WORDS = 180
MIN_CAPTION_BODY_FOR_EXPAND = 50  # below this, expand pass is unlikely to help — pad from article


def _caption_body_word_count(caption):
    """Count words in caption excluding #hashtag tokens (body-only)."""
    if not caption or not str(caption).strip():
        return 0
    without_tags = re.sub(r"#\w+", " ", str(caption))
    return len(without_tags.split())


def _append_context_for_longer_caption(caption, article, target_body_words=TARGET_CAPTION_BODY_WORDS):
    """Append article description sentences + boilerplate until body word count is closer to target."""
    wc = _caption_body_word_count(caption)
    if wc >= target_body_words:
        return caption
    desc = (article.get("description") or article.get("summary") or "").strip()
    boiler = (
        "What it means for markets: This development has direct read-through for rates, risk assets, and sector leadership. "
        "Investors are recalibrating while policy makers and executives issue fresh guidance. "
        "The next catalysts will be official data, earnings commentary, and cross-asset flows. "
        "Where do you think this heads next — a sustained move or a snapback? Comment below, tag someone who follows this space, and follow for more breakdowns."
    )
    chunks = []
    if desc:
        sentences = re.split(r"(?<=[.!?])\s+", desc)
        for s in sentences:
            s = s.strip()
            if len(s) < 20:
                continue
            chunks.append(s)
            merged = caption.rstrip() + "\n\n" + "\n\n".join(chunks)
            if _caption_body_word_count(merged) >= target_body_words - 20:
                break
    out = caption.rstrip()
    if chunks:
        out += "\n\n" + "\n\n".join(chunks)
    if _caption_body_word_count(out) < target_body_words - 40:
        out += "\n\n" + boiler
    return out


def generate_facebook_caption(article, system_prompt=None, topic_theme=None, tone=None, hashtag_focus=None):
    """
    Generate a professional-grade Facebook caption (180–250 words). Uses Ollama; if unavailable uses Gemini when GEMINI_API_KEY is set; else template caption.
    system_prompt: persona (e.g. "You are an expert real estate content creator...").
    topic_theme: focus for this page (e.g. "Market trends and home buying tips").
    tone: optional (e.g. "professional but approachable", "urgent and concise").
    hashtag_focus: optional (e.g. "#RealEstate #HomeBuying") to prioritize in hashtags.
    """
    print("Generating Facebook caption...")
    persona = system_prompt or "You are a senior US news editor writing for Facebook. You write long, engaging, descriptive captions that explain why the news matters."
    theme_block = ""
    if topic_theme:
        theme_block = f"""
Your page's content theme: {topic_theme}.
Tie the news to this theme when relevant. Speak directly to an audience interested in this topic.
"""
    tone_line = f"\nTone: {tone}.\n" if tone else ""
    hashtag_line = ""
    if hashtag_focus:
        hashtag_line = f"\nInclude these hashtags (or close variants) where relevant: {hashtag_focus}. Then add 15–25 more relevant hashtags.\n"
    desc = (article.get("description") or article.get("summary") or "")[:1200]
    prompt = f"""
{persona}
{theme_block}{tone_line}
Based on this BREAKING NEWS article, write a FULL, DESCRIPTIVE Facebook caption. Short or minimal captions are NOT acceptable.

Title: {article.get('title') or 'Breaking News'}
Description: {desc}

STRICT REQUIREMENTS:
- Length: You MUST write 180–250 words of body text (before hashtags). Count your words; if under 180, add more context and analysis.
- Hook: Start with one of "BREAKING:", "JUST IN:", "DEVELOPING:", or "UPDATE:" and a bold, specific statement (not generic). Vary the hook so not every post looks the same. Use power words where appropriate (key, major, exclusive, revealed).
- Body: Explain what happened, why it matters, who is affected, and what experts or markets are saying. Use 2–3 short paragraphs if needed.
- Insight: Include 3–4 analyst-style takeaways (use em dashes to separate).
- CTA (viral): End with a strong call-to-action that drives comments and shares. Use one or combine: a clear question ("What do you think?"), "Tag someone who needs to see this", "Share if this matters to you", "Comment below with your take", "Follow for more breaking news", or "Save this post for later". Make the CTA specific to the story when possible.
- Emojis: Use 4–8 relevant emojis in the caption to make the post more viral and engaging. Place them at the hook (e.g. 📰 BREAKING: or 🔥 JUST IN:), between key points, or after the CTA. Choose emojis that match the story (e.g. 📊 for data, 💼 for business, ⚖️ for law, 🌍 for global news). Do not put emojis inside hashtags.
- Hashtags: After the full caption text, append 20–30 relevant hashtags.{hashtag_line} No spaces inside hashtags.

Return ONLY the caption text followed by hashtags. No preamble, no "Here is the caption", no labels.
IMPORTANT: Write at least 180 words of body text. Two or three paragraphs. Use emojis to boost engagement. Then hashtags. Short captions are rejected.
"""
    _min_caption_body_gemini = 90  # After padding, require at least this much body or fall back to template

    try:
        from ollama_client import ollama_available, ollama_generate_text

        if ollama_available():
            opts = {}
            try:
                from config import OLLAMA_CAPTION_NUM_PREDICT

                if OLLAMA_CAPTION_NUM_PREDICT and int(OLLAMA_CAPTION_NUM_PREDICT) > 0:
                    opts["num_predict"] = int(OLLAMA_CAPTION_NUM_PREDICT)
            except (ImportError, TypeError, ValueError):
                opts["num_predict"] = 1024
            caption = ollama_generate_text(prompt, options=opts if opts else {"num_predict": 1024})
            if caption:
                body_wc = _caption_body_word_count(caption)
                if body_wc < TARGET_CAPTION_BODY_WORDS and body_wc >= MIN_CAPTION_BODY_FOR_EXPAND:
                    expand_prompt = f"""The caption below is too short for Facebook. Expand it to at least {TARGET_CAPTION_BODY_WORDS} words of body text (do not count hashtags toward that minimum). Keep the hook and tone. Add: what happened, why it matters, who is affected, 3–4 analyst-style takeaways (em dash separated), and a strong CTA. Use 4–8 emojis in the body. Keep existing hashtags at the end; if there are no hashtags, add 20–30 relevant ones on new lines at the end. Output only the full caption.

{caption}"""
                    expanded = ollama_generate_text(expand_prompt, options=opts if opts else {"num_predict": 1024})
                    if expanded and _caption_body_word_count(expanded) > body_wc:
                        caption = expanded
                        body_wc = _caption_body_word_count(caption)
                if body_wc < TARGET_CAPTION_BODY_WORDS:
                    caption = _append_context_for_longer_caption(caption, article, TARGET_CAPTION_BODY_WORDS)
                    body_wc = _caption_body_word_count(caption)
                if body_wc < 60 and "#" not in caption:
                    caption = (
                        caption.rstrip()
                        + "\n\n#BreakingNews #WorldNews #Markets #Economy #Analysis #Policy #USNews #Finance"
                    )
                print(f"Caption from Ollama (body ~{body_wc} words; total tokens {len(caption.split())})")
                return caption
    except Exception as e:
        print(f"Ollama caption failed: {e}, using fallback caption")

    try:
        from config import GEMINI_API_KEY

        if GEMINI_API_KEY and GEMINI_API_KEY.strip():
            caption = _generate_caption_with_gemini(article, persona, theme_block, tone_line, hashtag_line, desc)
            if caption:
                if _caption_body_word_count(caption) < TARGET_CAPTION_BODY_WORDS:
                    caption = _append_context_for_longer_caption(caption, article, TARGET_CAPTION_BODY_WORDS)
                if _caption_body_word_count(caption) >= _min_caption_body_gemini:
                    print(
                        f"Caption generated with Gemini (Ollama unavailable), body ~{_caption_body_word_count(caption)} words"
                    )
                    return caption
    except Exception:
        pass
    return generate_fallback_caption(article)


def _generate_caption_with_gemini(article, persona, theme_block, tone_line, hashtag_line, desc):
    """Generate 180–250 word caption using Gemini when Ollama is not available (e.g. RunPod)."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""{persona}{theme_block}{tone_line}
Based on this BREAKING NEWS article, write a FULL Facebook caption. You MUST write 180–250 words of body (then 20–30 hashtags).

Title: {article.get('title') or 'Breaking News'}
Description: {desc[:800]}

Requirements: Start with BREAKING: or JUST IN: or DEVELOPING: and a bold statement. Use 4–8 relevant emojis. Then 2–3 paragraphs: what happened, why it matters, who is affected. End with a viral CTA: a question, "Tag someone who needs to see this", "Share if you agree", "Comment below 👇", or "Follow for more". Then 20–30 hashtags. No emojis inside hashtags.
Output only the caption."""
        resp = model.generate_content(prompt)
        if resp and resp.text:
            return resp.text.strip()
    except Exception:
        pass
    return None

def generate_fallback_caption(article):
    """Fallback caption when Ollama is unavailable or fails — descriptive so posts are not too short."""
    title = (article.get("title") or "Breaking News").strip()
    desc = (article.get("description") or article.get("summary") or "").strip()
    # Use up to ~400 chars of description so fallback is still substantive
    desc_block = desc[:400] + ("..." if len(desc) > 400 else "") if desc else "Details are still emerging."
    return f"""📰 🚨 BREAKING: {title}

{desc_block}

💡 What it means: This development has significant implications for markets, policy makers, and the broader economy. Analysts are watching for follow-up moves and official reactions. Stay informed as this story develops.

🔥 Where do you think this is heading? Comment below 👇 Tag someone who needs to see this — and follow for more breaking news 📰

#BreakingNews #WorldNews #USNews #EUNews #CurrentEvents #News #Update #Alert #Trending #Viral #Important #Analysis #Insight #Policy #Economy #Politics"""

def generate_post_video(article):
    """
    Generate a local branded MP4 using the existing image-post pipeline.
    """
    print("Generating post video from branded image...")
    
    try:
        image_path = generate_post_image_fallback(article, output_path=os.path.join(_CONTENT_GEN_BASE, "post_video_source.jpg"))
        image_path = os.path.abspath(image_path) if image_path else None
        if not image_path or not os.path.exists(image_path):
            print("Video generation failed: branded source image missing.")
            return None

        clip_fn = globals().get("image_to_video_clip")
        if clip_fn is None:
            from image_to_video_clip import image_to_video_clip as clip_fn

        final_video_path = clip_fn(
            image_path,
            output_path=os.path.join(_CONTENT_GEN_BASE, "post_video.mp4"),
            duration_seconds=8,
            width=720,
            height=900,
            effect="zoom",
            fps=30,
        )
        try:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

        if final_video_path and os.path.exists(final_video_path):
            return final_video_path
        print("Local video render failed. Skipping this cycle (video-only mode).")
        return None

    except Exception as e:
        print(f"Error generating video: {e}")
        return None

def generate_video_prompt_with_gemini(article):
    """Use Gemini to create a detailed video prompt for Veo 3"""
    print("Creating video prompt with Gemini...")
    
    try:
        prompt = f"""
        Create a highly detailed, cinematic video prompt for Google's Veo 3 to generate an 8-second 1080p, 16:9 video that directly represents this specific news story:
        
        NEWS STORY: {article['title']}
        DESCRIPTION: {article['description']}
        
        The video MUST visually represent the actual news story with these specific elements:
        - Show the main subject/object from the news (e.g., if it's about Doritos, show Doritos; if it's about AI, show AI elements)
        - Include visual metaphors for the key concepts in the story
        - Use appropriate settings (school, airport, office, etc. based on the story)
        - Show the dramatic/important moment from the news
        - Include relevant people/situations (teenagers, police, officials, etc. as appropriate)
        
        Technical requirements:
        - Duration: exactly 8 seconds; aspect: 16:9; resolution: 1080p
        - Cinematic style: dramatic lighting, professional news documentary style
        - Camera work: slow push-in, parallax movement, shallow depth of field
        - Mood: urgent, dramatic, newsworthy
        - No on-screen text, no logos, no identifiable private individuals
        - Must be directly related to the specific news story content
        
        Output: A single-paragraph visual prompt that directly represents this news story, no generic content.
        """
        
        g = _genai()
        model = g.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        video_prompt = response.text.strip()
        
        print(f"Video prompt generated: {video_prompt[:100]}...")
        return video_prompt
        
    except Exception as e:
        print(f"Error generating video prompt: {e}")
        # Fallback prompt
        return f"Professional news documentary style 8-second video representing: {article['title']}. High quality, cinematic, 1080p, 16:9 aspect ratio, with appropriate audio."

def _is_image_prompt_refusal(text):
    """True if the model refused (e.g. 'I can't create...') instead of returning a real prompt."""
    if not text or len(text.strip()) < 20:
        return True
    t = text.strip().lower()
    refusal_phrases = (
        "i can't", "i cannot", "i'm not able", "i am not able", "i won't", "i will not",
        "i don't", "i do not", "i'm unable", "i am unable", "is there anything else i can help",
        "can i help you with something else", "can i help you with",
        "real person", "depict a real person", "specific individual", "compromising or uncomfortable",
        "cannot create", "can't create", "unable to create", "refuse", "cannot assist",
        "create an image prompt that depicts", "depicts a violent", "violent act", "such as breaking",
        "i can't create an image prompt"
    )
    return any(p in t for p in refusal_phrases)


def _image_prompt_template_fallback(article):
    """Template-based image prompt when Ollama is unavailable or fails. Uses summary so the image conveys the news properly. When names are mentioned, requires showing them in photorealistic style (classic mode only)."""
    title = (article.get("title") or "")[:80]
    summary = (article.get("description") or article.get("summary") or title)[:300]
    try:
        from config import IMAGE_VISUAL_MODE, INSTITUTIONAL_ACCENT_HEX
    except ImportError:
        IMAGE_VISUAL_MODE = "classic"
        INSTITUTIONAL_ACCENT_HEX = "#00B8D4"
    if IMAGE_VISUAL_MODE == "institutional":
        aspect = f"{SENSATIONAL_ASPECT_RATIO} portrait" if USE_SENSATIONAL_BREAKING_TEMPLATE else "4:3"
        summary_bit = f" Narrative mapped to abstract macro/risk dashboard: {summary}" if summary else ""
        fallback = (
            f"Dark-mode institutional market visualization for the story: {title}.{summary_bit} "
            f"Sleek minimalist charts—abstract structural shifts, break-of-structure and liquidity-sweep geometry as light and "
            f"lines only; cross-asset style panels; no readable tickers. Deep navy and slate, stark white grid hints, "
            f"glowing accent ({INSTITUTIONAL_ACCENT_HEX}), subtle film grain, institutional terminal UI; calculated professional "
            f"edge, not retail noise. No people, no faces, no stock-photo office tropes. "
            f"Bottom third: dark navy footer for overlay; no text, logos, or watermarks. {aspect}."
        )
    else:
        main_figure_line = " The central subject is the main person at the center of this news—shown in role-appropriate attire and setting, clear expression and posture, so the crux of the story is obvious."
        names = _extract_mentioned_names(article)
        names_line = f" The image MUST show the named person(s): {', '.join(names)}. Depict them in photorealistic, documentary style—realistic human appearance as in real news photographs." if names else ""
        summary_line = f" The scene must convey the summary of the news: {summary}. Show the specific event, setting, and mood so a viewer understands what the story is about." if summary and summary != title else ""
        real_line = " All people must look real: photorealistic, as in real news photography—realistic faces and bodies, not illustrated or cartoon."
        if USE_SENSATIONAL_BREAKING_TEMPLATE:
            fallback = f"Hyperrealistic breaking news scene that conveys the summary of the news: {title}. {summary_line}{names_line} The image prominently features the main person(s) concerned—in detailed, context-appropriate setting with dramatic lighting and expression that match the story. Photorealistic, real-photograph style. High contrast, sharp focus, vivid saturated colors, {SENSATIONAL_ASPECT_RATIO} vertical portrait (mobile). No text."
        else:
            fallback = f"Professional news photography that conveys the summary of the news: {title}. {summary_line}{names_line} Central subject is the main figure(s) in the story, in specific setting and attire with expressive posture that reflects the story. Photorealistic, real-photograph style. High quality, dramatic lighting, vivid colors, no text."
        fallback = (fallback or "").strip() + main_figure_line + real_line
    try:
        from minimal_overlay import get_country_code_for_article, get_country_name_for_prompt
        cc = get_country_code_for_article(article)
        country_name = get_country_name_for_prompt(cc) if cc else None
        if country_name:
            if IMAGE_VISUAL_MODE == "institutional":
                fallback = (fallback or "").strip() + f" Subtle abstract geographic mood for {country_name} via color temperature or light gradient only—no landmarks, no text."
            else:
                fallback = (fallback or "").strip() + f" The scene should subtly depict or evoke the source region: {country_name}—e.g. architecture, landscape, or cultural cues—without text."
    except ImportError:
        pass
    return fallback


def _title_words_to_avoid(article, max_words=14):
    """Words from the title (4+ chars, not stop words) that must not appear in the image prompt so the model does not draw them."""
    title = (article.get("title") or "").strip()
    if not title:
        return []
    stop = {"the", "and", "for", "with", "this", "that", "from", "have", "has", "had", "are", "was", "were", "been", "said", "says", "will", "would", "could", "should", "about", "into", "over", "after", "when", "where", "which", "their", "there", "what", "than", "then", "not", "but", "out", "all", "can", "her", "his", "one", "our", "who", "its"}
    words = [w.strip(".,;:!?'\"") for w in title.split()[:max_words] if len(w.strip(".,;:!?'\"")) >= 4 and w.strip(".,;:!?'\"").lower() not in stop]
    return list(dict.fromkeys(words))[:20]


def _extract_mentioned_names(article, max_names=5):
    """Extract likely person names from title and summary (e.g. 'Joe Biden', 'Rishi Sunak') so the prompt can require showing them. Returns list of strings."""
    text = " ".join([
        (article.get("title") or ""),
        (article.get("summary") or article.get("description") or ""),
    ]).strip()[:600]
    if not text:
        return []
    words = text.replace(",", " ").replace(":", " ").split()
    names = []
    i = 0
    while i < len(words) and len(names) < max_names:
        w = words[i].strip(".,;:!?'\"()")
        if len(w) >= 2 and w[0].isupper() and w[1:].lower() == w[1:]:
            run = [w]
            j = i + 1
            while j < len(words) and len(run) <= 2:
                nw = words[j].strip(".,;:!?'\"()")
                if len(nw) >= 2 and nw[0].isupper():
                    run.append(nw)
                    j += 1
                else:
                    break
            if run and run[0].lower() not in ("breaking", "news", "says", "said", "new", "uk", "us", "eu", "ceo", "pm", "mr", "mrs", "ms", "dr", "the", "prime", "minister", "president", "chief", "secretary", "government", "court", "house", "white", "downing"):
                name = " ".join(run)
                if name not in names:
                    names.append(name)
            i = j
        else:
            i += 1
    return names[:max_names]


def generate_image_prompt_with_gemini(article, system_prompt=None, topic_theme=None, visual_style=None):
    """Create a viral news image prompt using Ollama only. Fallback: template prompt. (Name kept for call compatibility.)"""
    print("Creating image prompt...")
    title = (article.get("title") or "")[:500]
    summary = (article.get("summary") or article.get("description") or title)[:800]
    theme_line = f" This image is for a page whose theme is: {topic_theme}. When the story allows, lean visuals toward this theme (e.g. real estate → property/markets, fitness → energy/activity)." if topic_theme else ""
    _default_vs = None
    try:
        _default_vs = get_default_visual_style_for_image_prompt()
    except Exception:
        _default_vs = None
    effective_style = visual_style or _default_vs
    style_line = f" Visual style for this page: {effective_style}." if effective_style else ""
    avoid_words = _title_words_to_avoid(article)
    avoid_line = f" Do NOT use any of these words in your output (they would be drawn as text): {', '.join(avoid_words)}." if avoid_words else ""
    try:
        from config import IMAGE_VISUAL_MODE, INSTITUTIONAL_ACCENT_HEX
    except ImportError:
        IMAGE_VISUAL_MODE = "classic"
        INSTITUTIONAL_ACCENT_HEX = "#00B8D4"
    _institutional = IMAGE_VISUAL_MODE == "institutional"
    mentioned_names = [] if _institutional else _extract_mentioned_names(article)
    names_line = ""
    real_style_line = ""
    if not _institutional:
        names_line = f"\n\nNAMED PERSONS (critical): The news mentions these people: {', '.join(mentioned_names)}. The image MUST show them. Include each as a distinct figure in the scene (central subject and any others in the frame). Describe each so they are clearly present—role, attire, position, expression. Do not omit anyone named." if mentioned_names else ""
        real_style_line = " All people in the image must look REAL: photorealistic, as in real news photography—realistic human faces, skin, and bodies; documentary or press-photo style; not illustrated, not cartoon, not stylized. The image should look like a real photograph of real people."
    try:
        aspect = __import__("config", fromlist=["IMAGE_ASPECT_RATIO"]).IMAGE_ASPECT_RATIO
    except Exception:
        aspect = "4:3"
    if USE_SENSATIONAL_BREAKING_TEMPLATE:
        aspect = SENSATIONAL_ASPECT_RATIO

    if _institutional:
        accent = INSTITUTIONAL_ACCENT_HEX
        if USE_SENSATIONAL_BREAKING_TEMPLATE:
            prompt = f"""Act as an expert in financial data visualization and terminal UI design. Create ONE detailed image prompt for a dark-mode institutional dashboard—abstract only. Focus on market MECHANICS, not generic stock imagery. NO photorealistic people, NO faces, NO portraits, NO businesspeople holding heads, handshakes, or cheesy office stock photos. Map the news to macro/risk/liquidity concepts as GEOMETRY and LIGHT: structural shifts, implied break-of-structure, liquidity sweeps and zones, volatility surfaces, cross-asset monitors, order-flow–like ribbons—all without readable tickers, numbers, or labels.{theme_line}{style_line}

News: {title}
Summary: {summary}

CONVEY THE STORY (abstract): Translate tension, direction, and magnitude from the summary into minimalist chart-like shapes, glow intensity, and spatial layout—institutional-grade data visualization, not literal people or places.

VIBE: Calculated, professional, sophisticated—signals analytical edge, not retail noise.

STYLE LOCK: Deep navy (#0a1020) and slate gray; stark white only for thin grid lines; sharp glowing accent lines in {accent}; sleek minimal charts; premium Bloomberg-terminal / institutional fintech feel; subtle film grain; restrained mood.

LAYOUT: Aspect ratio {aspect} (vertical portrait, mobile). Upper area: abstract price action, volume blocks, zones as blurred geometry (no legible text). Reserve bottom-left for a small empty badge zone (no text drawn). Bottom third: dark navy panel / chart footer for overlay—no words, no logos, no watermarks.

FORBIDDEN: Named persons, crowds, offices with people, vivid candy saturation, magazine layouts, readable text.

CRITICAL: Describe ONLY non-text visuals.{avoid_line} Output only one paragraph image prompt."""
        else:
            prompt = f"""Act as an expert in financial data visualization. Create ONE detailed image prompt for a dark institutional terminal / macro dashboard—sleek minimalist charts and structural market mechanics only. NO people, NO faces, NO photorealistic humans.{theme_line}{style_line}

News: {title}
Summary: {summary}

Map the narrative to abstract macro or risk visualization: dashboards, liquidity and structure concepts as geometry and light—break-of-structure / sweep motifs as abstract lines and fills only—no readable text or logos.

VIBE: Professional edge, not retail noise.

STYLE: Deep navy and slate; glowing accent {accent}; institutional-grade data viz; subtle film grain. Aspect ratio {aspect}. Clean negative space at top. Bottom: dark navy footer zone for overlay.

FORBIDDEN: Stock-photo people, portraits, vivid saturated poster colors, watermarks, legible text.

CRITICAL:{avoid_line} One paragraph only. No preamble."""
    elif USE_SENSATIONAL_BREAKING_TEMPLATE:
        prompt = f"""Act as an expert editorial photographer. Create a single, highly detailed hyperrealistic image prompt that directly illustrates THIS news story. The image must convey the SUMMARY of the news properly: a viewer should understand what the story is about—what happened, who is involved, where, and the key outcome or takeaway—from the visual alone. No generic imagery; every element must support that summary.{theme_line}{style_line} Output only the image prompt paragraph, nothing else.

IMAGE STYLE (mandatory): Photorealistic documentary/news photography only—like Reuters, AP, or broadcast B-roll. Do NOT describe abstract financial charts, dark-mode trading terminals, candlestick graphics, liquidity maps, or any "dashboard / data viz template" look. Show real places and people (press conferences, exchanges, city finance districts, hearings, corporate settings) as a real camera would capture them.

News: {title}
Summary: {summary}
{names_line}

CONVEY THE SUMMARY: Base the scene strictly on the summary above. The visual must illustrate the specific event, decision, conflict, or situation described (e.g. "government announces X," "company faces backlash," "leader resigns," "deal agreed"). Include concrete details from the summary—location, type of place, mood (tension, relief, urgency), and any key objects or actions. The image should tell the same story as the summary in one glance.

MAIN FIGURE (critical): Identify the main person at the center of this story (and any other named persons). The image MUST prominently feature them so viewers immediately understand who the news is about. Describe each person in specific visual detail: role-appropriate attire, expression and body language that match the summary, and exact context (podium, courtroom, press conference, etc.). Do NOT use a generic "person"; the central subject(s) should embody the summary. If names are mentioned in the news, ensure those people are shown in the image.

REAL, PHOTOREALISTIC PEOPLE: Every person in the scene must look real—as in real news photography. Describe them so the image will be photorealistic: realistic human faces, skin texture, natural proportions, documentary or press-photo style. Not illustrated, not cartoon, not stylized. The result should look like a real photograph of real people.{real_style_line}

FORMAT: Aspect ratio {aspect} (vertical **4:5** portrait). CRITICAL: Describe ONLY the visual scene—objects, people, setting, lighting. Do NOT include any headline, quote, or phrase that could be rendered as text.{avoid_line} No magazine-style text. The headline is added in a separate layer; this prompt is for a text-free scene only.

VISUAL PROMPT (one detailed paragraph):
- Upper two-thirds: A rich, specific scene that conveys the summary—centered on the main figure(s), with all named persons shown if the news mentions names. Setting and situation must directly reflect the news. Include props and supporting elements that reinforce the summary. Lighting and color mood should match the story. All persons must be described so they appear photorealistic—realistic human appearance as in real photographs.
- Reserve a small area bottom-left for a graphic badge (no text drawn).
- Reserve bottom-right for a secondary moment from the same story.
- Bottom third: Solid black rectangle; no words.

Style: Hyper-realistic documentary/news photography—real photographs of real people. High contrast, sharp focus, cinematic. Vivid, saturated colors. No text, no words, no headlines in the image.

Output only the single paragraph image prompt. Describe only what to draw visually. Do not include any phrase that could appear as text on the image."""
    else:
        prompt = f"""Act as an expert social media strategist and editorial illustrator. Your goal is to convert the following news into a highly detailed image concept for Facebook. The image must convey the SUMMARY of the news properly: a viewer should understand what the story is about—what happened, who is involved, and the key outcome—from the visual alone. No generic imagery; every element must support that summary.{theme_line}{style_line} Output only the final image prompt, nothing else.

IMAGE STYLE (mandatory): Photorealistic news/editorial photography only. No abstract chart terminals, no financial-dashboard or data-viz templates—real-world scenes and people as in press photography.

News: {title}
Summary: {summary}
{names_line}

CONVEY THE SUMMARY: Base the scene strictly on the summary above. The visual must illustrate the specific event, decision, conflict, or situation. Include concrete details from the summary—where it happens, type of place, mood, and key objects or actions. The image should tell the same story as the summary in one glance.

MAIN FIGURE (critical): Identify the main person at the center of this story (and any other named persons). The image MUST prominently feature them as the central subject(s). Describe each in specific visual detail: attire, expression and body language that match the summary, and exact context. If names are mentioned in the news, ensure those people are shown in the image. The central subject(s) should embody the summary—not a generic silhouette.

REAL, PHOTOREALISTIC PEOPLE: Every person in the scene must look real—as in real news photography. Describe them so the image will be photorealistic: realistic human faces, skin texture, natural proportions, documentary or press-photo style. Not illustrated, not cartoon. The result should look like a real photograph of real people.{real_style_line}

TECHNICAL SPECS:
Aspect ratio: {aspect}. Composition: leave clean negative space at the top (no text will be overlaid). The main figure(s) and setting together must convey the summary of the news properly.

VISUAL PROMPT (one detailed paragraph):
- Subject: The main figure(s) from the news—all named persons if the news mentions names—in concrete detail (attire, expression, gesture). Photorealistic, as in real photographs. Add supporting elements that reinforce the summary (documents, screens, crowd, location, key objects from the story).
- Setting: Specific place and atmosphere that match the summary (boardroom, courtroom, parliament, street, etc.). Include mood (tension, relief, urgency) so the summary is clear.
- Style: Cinematic editorial photography or hyper-realistic render—real photographs of real people. Vivid, saturated colors; premium and shareable.
- Lighting/Mood: Match the story (dramatic for conflict, warmer for resolution, etc.). Rich, appealing palette so the image conveys the summary and is visually striking.

Avoid: visual clutter, watermarks, distorted faces, generic stock tropes. CRITICAL: Do not include any headline or quote.{avoid_line} Describe only the visual scene. The headline is overlaid separately; this image must be text-free. The image must convey the summary of the news properly. People must look real—photorealistic, as in real news photography.

Output only the single paragraph image prompt. No preamble or labels."""
    try:
        from ollama_client import ollama_available, ollama_generate_text

        if ollama_available():
            image_prompt = ollama_generate_text(prompt)
            if image_prompt and not _is_image_prompt_refusal(image_prompt):
                print(f"Image prompt generated with Ollama: {image_prompt[:100]}...")
                out = image_prompt.strip()
                try:
                    from minimal_overlay import get_country_code_for_article, get_country_name_for_prompt

                    cc = get_country_code_for_article(article)
                    country_name = get_country_name_for_prompt(cc) if cc else None
                    if country_name:
                        if _institutional:
                            out = (out or "").strip() + f" Subtle abstract geographic mood for {country_name} via color temperature or light gradient only—no landmarks, no text."
                        else:
                            out = (out or "").strip() + f" The scene should subtly depict or evoke the source region: {country_name}—e.g. architecture, landscape, or cultural cues—without text."
                except ImportError:
                    pass
                return out
            if image_prompt and _is_image_prompt_refusal(image_prompt):
                print("Ollama returned a refusal; using template fallback for image prompt.")
    except Exception as e:
        print(f"Ollama image prompt failed: {e}, using template fallback")
    return _image_prompt_template_fallback(article)


def get_short_headline_for_overlay(article, max_words=15):
    """
    Return a complete, meaningful headline that summarizes the news in at most max_words.
    Uses Ollama to summarize; fallback: first sentence of title (trimmed to max_words) or first max_words words.
    """
    title = (article.get("title") or "").strip()
    desc = (article.get("description") or article.get("summary") or "").strip()[:200]
    if not title:
        return "Breaking News"
    prompt = f"""Summarize this news in one complete, meaningful sentence. Use {max_words} words or fewer. The sentence must be grammatically complete and capture the main point. Output only that sentence, no quotes or prefix.

News: {title}
{f'Context: {desc}' if desc else ''}"""

    try:
        from ollama_client import ollama_available, ollama_generate_text

        if ollama_available():
            out = ollama_generate_text(prompt)
            if out:
                s = out.strip()
                if len(s) >= 2 and (s.startswith('"') and s.endswith('"') or s.startswith("'") and s.endswith("'")):
                    s = s[1:-1].strip()
                w = s.split()
                if w and len(w) <= max_words:
                    return s[:250] if len(s) > 250 else s
                if w and len(w) > max_words:
                    trimmed = " ".join(w[:max_words]).rstrip(".,;:")
                    return trimmed + "\u2026" if trimmed else " ".join(title.split()[:max_words])
    except Exception:
        pass

    # Fallback: first sentence of title (complete phrase), then trim to max_words
    for sep in (". ", "! ", "? ", " – ", " - "):
        if sep in title:
            first = title.split(sep)[0].strip()
            if first:
                words = first.split()[:max_words]
                return " ".join(words).strip() or "Breaking News"
    words = title.split()[:max_words]
    return " ".join(words).strip() or "Breaking News"


def _sanitize_image_prompt_no_headline(image_prompt, article):
    """Remove article headline/title words and phrases from the image prompt so the diffusion model does not draw them (headline is only in our overlay)."""
    if not image_prompt or not isinstance(image_prompt, str):
        return image_prompt
    import re
    out = image_prompt
    title = (article.get("title") or "").strip()
    summary = (article.get("description") or article.get("summary") or "")[:300]
    # 1) Replace exact phrases (longest first)
    if title and len(title) >= 8:
        tw = title.split()
        for n in range(min(14, len(tw)), 0, -1):
            p = " ".join(tw[:n])
            if len(p) >= 8 and p in out:
                out = out.replace(p, "the story")
    # 2) Remove quoted strings (headline-like)
    for quoted in re.findall(r'"([^"]{12,100})"', out):
        if quoted.strip():
            out = out.replace('"' + quoted + '"', "the story")
    for quoted in re.findall(r"'([^']{12,100})'", out):
        if quoted.strip():
            out = out.replace("'" + quoted + "'", "the story")
    # 3) Strip every title word (4+ chars) from the prompt so the model never sees them
    if title:
        stop = {"the", "and", "for", "with", "this", "that", "from", "have", "has", "had", "are", "was", "were", "been", "said", "says", "will", "would", "could", "should", "about", "into", "over", "after", "when", "where", "which", "their", "there", "what", "than", "then"}
        title_words = set(w.strip(".,;:!?'\"") for w in title.split() if len(w.strip(".,;:!?'\"")) >= 4 and w.strip(".,;:!?'\"").lower() not in stop)
        for word in title_words:
            if len(word) < 4:
                continue
            pat = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
            out = pat.sub("scene", out)
    if summary:
        sw = summary.split()[:8]
        p = " ".join(sw)
        if len(p) >= 12 and p in out:
            out = out.replace(p, "the story")
    return out


def _append_comprehensive_news_visual_directive(prompt: str | None, article) -> str:
    """Extra diffusion instructions so the frame encodes summary, stakes, and setting (no readable text in-image)."""
    p = (prompt or "").strip()
    bits: list[str] = []
    summ = (article.get("summary") or article.get("description") or "").strip()
    if summ and len(summ) > 40:
        bits.append(
            "Integrate these story beats into composition, props, wardrobe, environment, and emotional tone "
            f"(do not render as text): {summ[:520]}"
        )
    title = (article.get("title") or "").strip()
    if title and len(title) > 20:
        bits.append(
            "The single image must make the core news event and its implications obvious to a viewer who has not read the article—"
            "specific setting, key action or decision, and human reactions where relevant."
        )
    if (article.get("source") or "").strip():
        bits.append(
            "Subtle broadcast-news gravitas (no logos, watermarks, or readable text); serious editorial mood only."
        )
    if not bits:
        return p
    return p + " " + " ".join(bits)


def _append_comprehensive_news_visual_directive_for_cursor(
    prompt: str | None, article, *, pil_headline_overlay: bool = True
) -> str:
    """Extra scene instructions for Cursor image tool. If ``pil_headline_overlay`` (default): no generator headline."""
    p = (prompt or "").strip()
    bits: list[str] = []
    summ = (article.get("summary") or article.get("description") or "").strip()
    if summ and len(summ) > 40:
        bits.append(
            "Integrate these story beats into composition, props, wardrobe, environment, and emotional tone "
            f"(show the story through action and setting—do not paste the summary as body text): {summ[:520]}"
        )
    title = (article.get("title") or "").strip()
    if title and len(title) > 20:
        bits.append(
            "The single image must make the core news event and its implications obvious—specific setting, "
            "key action or decision, and human reactions where relevant."
        )
    if pil_headline_overlay:
        bits.append(
            "Viral USA breaking-news photoreal look; **no headline, chyron, or lower-third text in the image**—"
            "title typography is added in post with correct 4:5 margins. No fake TV network logos; no watermarks."
        )
    else:
        bits.append(
            "Viral USA breaking-news social share look: high-impact photoreal composition; bold readable headline "
            "typography is required (see HEADLINE ON IMAGE block)—keep that headline **inside** the safe margins described there "
            "(not against the frame edges). No fake TV network logos; no watermarks."
        )
    if not bits:
        return p
    return p + " " + " ".join(bits)


def _cursor_headline_geometry_block(title: str) -> str:
    """
    Hard layout rules for Cursor / image-model headline rendering (pixels must stay inside frame).
    Length-dependent line-count hints reduce single-line overflow.
    """
    t = (title or "").strip()
    try:
        from config import CURSOR_HEADLINE_INSET_PCT as _inset
        inset = max(5, min(15, int(_inset)))
    except Exception:
        inset = 8
    hi = 100 - inset
    n = len(t)
    wc = len(t.split())
    if n <= 44:
        wrap = "Use **1-2 lines**. Target <=40 characters per line (including spaces)."
    elif n <= 90:
        wrap = "Use **at least 3 lines**. Target <=36 characters per line. Do **not** run one ultra-wide line."
    elif n <= 140:
        wrap = "Use **3-4 lines**. Target <=34 characters per line. **Reduce font size** until the block clearly fits."
    else:
        wrap = "Use **4-5 lines**. Target <=32 characters per line. **Smaller bold type** is required; never one or two giant lines."

    return (
        f"**SAFE ZONE (NON-NEGOTIABLE):** All headline letters, punctuation, shadows, and bar edges must lie strictly "
        f"between **{inset}%** and **{hi}%** of the image **width** (measuring from the left edge of the canvas)—"
        f"nothing may touch or cross the left or right frame border. Leave at least **{inset}%** empty margin to the **bottom** "
        f"frame edge (no descenders or bar clipped off). If in doubt, **shrink the type** and add line breaks.\n"
        f"**LEFT PADDING (CRITICAL):** The **first character** of the headline’s **first line** must start **at least {inset}%** "
        f"of the **total canvas width** to the **right** of the left frame edge—never flush, never “almost touching.” "
        f"Shift the **entire** headline bar as needed so **both** sides show clear padding.\n"
        f"**RIGHT PADDING (CRITICAL):** The **last character** of the **widest** line must end **at least {inset}%** "
        f"of the canvas width **before** the right frame edge—no line may run flush to the right border; shrink type or wrap.\n"
        f"**WRAP ({n} characters, {wc} words):** {wrap}\n"
        "**VERIFY:** Mentally check that the widest line would still clear both side margins; otherwise break the line or shrink text."
    )


def _cursor_tool_mandatory_headline_suffix(article) -> str:
    """Exact headline text the image tool must render on-image for US viral feeds."""
    ht = (article.get("title") or article.get("headline") or "").strip()
    if not ht:
        return ""
    geo = _cursor_headline_geometry_block(ht)
    return (
        "\n\n--- HEADLINE ON IMAGE (MANDATORY — ONLY SOURCE) ---\n"
        "You must render the following EXACT headline **in this image**, with **viral breaking-news** cable/social typography: "
        "high-urgency lower-third or top strip; white and/or yellow on deep red, navy, or black; thick clean sans-serif; "
        "looks like a shareable Facebook/TV grab (not a corporate deck).\n"
        "This tool pass is the **only** place headline text appears—no follow-up text layer will fix or replace it. "
        "Word-for-word identical to below; no shortening or paraphrase.\n"
        f"{geo}\n"
        f"{ht}\n\n"
        "The photographic scene must still show the crux of the story; headline typography is prominent, fully inside the frame, and readable."
    )


def _is_probably_blank_generated_image(image_path):
    """Reject near-black generator failures before overlay/posting."""
    if not image_path or not os.path.exists(image_path):
        return True
    try:
        from PIL import Image, ImageStat

        with Image.open(image_path) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            mean = float(stat.mean[0]) if stat.mean else 0.0
            extrema = gray.getextrema() or (0, 0)
            max_px = int(extrema[1] or 0)
        return (mean <= 8.0 and max_px <= 24) or max_px <= 10
    except Exception as e:
        print(f"[WARN] Blank-image check skipped: {e}")
        return False


def _generate_image_with_single_safe_retry(image_prompt, output_path):
    """Generate once; if result is blank/near-black, retry once with safer settings."""
    image_path = generate_image_with_imagen(image_prompt, output_path=output_path)
    if not image_path or not os.path.exists(image_path):
        return image_path
    if not _is_probably_blank_generated_image(image_path):
        return image_path

    print("[WARN] Generated base image looks blank/near-black. Retrying once with safer settings...")
    try:
        os.remove(image_path)
    except OSError:
        pass

    try:
        _z_local = Z_IMAGE_LOCAL_DIFFUSERS_ONLY
    except NameError:
        _z_local = False
    if _z_local:
        old_env = {
            "IMGEN_FEB_WINDOWS_BFLOAT16": os.environ.get("IMGEN_FEB_WINDOWS_BFLOAT16"),
            "IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE": os.environ.get("IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE"),
        }
        try:
            os.environ["IMGEN_FEB_WINDOWS_BFLOAT16"] = "0"
            os.environ["IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE"] = "1"
            retry_path = generate_image_with_imagen(image_prompt, output_path=output_path, safer_retry=True)
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    else:
        old_env = {
            "IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST": os.environ.get("IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST"),
            "IMGEN_PREFER_RUNPOD_IMAGE_LOCAL": os.environ.get("IMGEN_PREFER_RUNPOD_IMAGE_LOCAL"),
            "IMGEN_FEB_WINDOWS_BFLOAT16": os.environ.get("IMGEN_FEB_WINDOWS_BFLOAT16"),
            "IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE": os.environ.get("IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE"),
        }
        try:
            os.environ["IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST"] = "0"
            os.environ["IMGEN_PREFER_RUNPOD_IMAGE_LOCAL"] = "0"
            os.environ["IMGEN_FEB_WINDOWS_BFLOAT16"] = "0"
            os.environ["IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE"] = "1"
            retry_path = generate_image_with_imagen(image_prompt, output_path=output_path, safer_retry=True)
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    if retry_path and os.path.exists(retry_path) and not _is_probably_blank_generated_image(retry_path):
        return retry_path
    print("[WARN] Safe retry also produced a blank/near-black base image. Skipping this post.")
    try:
        if retry_path and os.path.exists(retry_path):
            os.remove(retry_path)
    except OSError:
        pass
    return None


def _apply_post_image_overlays_and_label(image_path: str, article, *, video_scene_mode: bool = False):
    """Text removal (optional), breaking overlay, mandatory AI label. Returns ``image_path`` or ``None``."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        from config import REMOVE_TEXT_FROM_IMAGE, IMAGE_GENERATION_MODE as _igm
    except ImportError:
        REMOVE_TEXT_FROM_IMAGE = False
        _igm = "cursor_only"
    try:
        _cursor = (_igm or "cursor_only").strip().lower() == "cursor_only"
    except Exception:
        _cursor = False
    try:
        if REMOVE_TEXT_FROM_IMAGE and not _cursor:
            from text_removal import remove_text_from_image
            if remove_text_from_image(image_path):
                print("Removed text from generated image before overlay.")
        elif REMOVE_TEXT_FROM_IMAGE and _cursor:
            print("Skipping REMOVE_TEXT_FROM_IMAGE (cursor_only).")
    except ImportError:
        pass
    ai_label_in_overlay = False
    if video_scene_mode:
        return image_path
    if USE_SENSATIONAL_BREAKING_TEMPLATE:
        try:
            if USE_MINIMAL_BREAKING_OVERLAY:
                from minimal_overlay import apply_minimal_breaking_overlay
                try:
                    from design_config import MINIMAL_HEADLINE_MAX_WORDS
                except ImportError:
                    MINIMAL_HEADLINE_MAX_WORDS = 15
                try:
                    from config import CURSOR_USE_PIL_HEADLINE_OVERLAY as _cursor_pil_hl
                except ImportError:
                    _cursor_pil_hl = True
                if _cursor and not _cursor_pil_hl:
                    # Legacy: headline baked into Cursor / image-tool output only (often clips at 4:5 edges).
                    short_headline = ""
                elif _cursor and _cursor_pil_hl:
                    # Default: exact article title, typeset by PIL with margin-aware fit (reliable 4:5).
                    t = (article.get("title") or article.get("headline") or "").strip()
                    short_headline = (
                        t[:300]
                        if t
                        else get_short_headline_for_overlay(article, max_words=MINIMAL_HEADLINE_MAX_WORDS)
                    )
                else:
                    short_headline = get_short_headline_for_overlay(
                        article, max_words=MINIMAL_HEADLINE_MAX_WORDS
                    )
                design_context = None
                try:
                    from design_config import USE_DESIGN_AGENT, USE_DESIGN_AGENT_LLM_SCHEMA
                    if USE_DESIGN_AGENT:
                        from design_agent import get_design_context
                        design_context = get_design_context(
                            image_path, article, use_llm_schema=USE_DESIGN_AGENT_LLM_SCHEMA, use_color_agent=True
                        )
                except ImportError:
                    pass
                source_name = (article.get("source") or article.get("source_id") or "").strip()
                try:
                    from config import CURSOR_USE_PIL_HEADLINE_OVERLAY as _cph
                except ImportError:
                    _cph = True
                if _cursor and not _cph:
                    print("Applying overlay (Breaking News label, logo, source; headline is in-image from Cursor tool)...")
                elif _cursor and _cph:
                    print(
                        "Applying overlay (Breaking News label, logo, source + PIL headline box for 4:5-safe type)..."
                    )
                else:
                    print("Applying overlay (Breaking News label, logo, headline box, source)...")
                ok = apply_minimal_breaking_overlay(
                    image_path, headline=short_headline, design_context=design_context, source=source_name
                )
                if ok:
                    if _cursor and not _cph:
                        print("Applied minimal Breaking News overlay (top-left label + logo + source).")
                    elif _cursor and _cph:
                        print(
                            "Applied minimal Breaking News overlay (top-left label + bottom headline + logo + source)."
                        )
                    else:
                        print("Applied minimal Breaking News overlay (top-left label + bottom headline + logo + source).")
                    ai_label_in_overlay = True
                else:
                    print("Overlay did not apply (check errors above or design_config: USE_HEADLINE_BOX, SHOW_BREAKING_LABEL).")
            else:
                from sensational_overlay import apply_sensational_overlay
                headline = (article.get("title") or "")[:200]
                caption_line = (article.get("description") or article.get("summary") or "")[:80]
                design_context = None
                try:
                    from design_config import USE_DESIGN_AGENT, USE_DESIGN_AGENT_LLM_SCHEMA
                    if USE_DESIGN_AGENT:
                        from design_agent import get_design_context
                        design_context = get_design_context(
                            image_path, article, use_llm_schema=USE_DESIGN_AGENT_LLM_SCHEMA, use_color_agent=True
                        )
                except ImportError:
                    pass
                if apply_sensational_overlay(image_path, headline, caption=caption_line or None, design_context=design_context):
                    print("Applied Sensational Breaking News overlay.")
        except Exception as e:
            print(f"Breaking overlay skipped: {e}")
    if os.path.exists(image_path) and not ai_label_in_overlay:
        add_ai_generated_label(image_path)
    return image_path


def _crop_resize_rgb_to_45(rgb):
    """Center-crop to **4:5** (width:height), then resize to ``get_post_image_dimensions_45()``."""
    from PIL import Image

    tw, th = get_post_image_dimensions_45()
    w, h = rgb.size
    tgt = 4.0 / 5.0
    src_ratio = w / float(h)
    if src_ratio > tgt:
        new_w = max(1, int(round(h * tgt)))
        left = (w - new_w) // 2
        rgb = rgb.crop((left, 0, left + new_w, h))
    else:
        new_h = max(1, int(round(w / tgt)))
        top = (h - new_h) // 2
        rgb = rgb.crop((0, top, w, top + new_h))
    return rgb.resize((tw, th), Image.Resampling.LANCZOS)


def _crop_resize_rgb_to_45_cursor_inbound(rgb, *, _crop_mode_override: str | None = None):
    """
    Normalize Cursor-tool inbound stills to 4:5 target pixels.

    **cover** (default): uniform scale so the image **covers** the full 4:5 rectangle, then crops
    overflow (horizontal center, vertical **bottom-anchored** to favor lower-third headlines).

    **letterbox**: scale to fit **inside** target; pad with black—output is 4:5 but the photo does not fill it.

    **headline_safe** / **center**: crop-first legacy paths.
    """
    from PIL import Image

    if _crop_mode_override:
        mode = _crop_mode_override.strip().lower()
    else:
        try:
            from config import CURSOR_INBOUND_CROP_MODE as _mode
        except Exception:
            _mode = "cover"
        mode = (_mode or "cover").strip().lower()
    if mode not in ("headline_safe", "center", "letterbox", "cover"):
        mode = "cover"

    tw, th = get_post_image_dimensions_45()
    w, h = rgb.size
    if w <= 0 or h <= 0:
        return _crop_resize_rgb_to_45(rgb)

    if mode == "cover":
        scale = max(tw / float(w), th / float(h))
        nw = max(1, int(round(w * scale)))
        nh = max(1, int(round(h * scale)))
        scaled = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
        left = max(0, (nw - tw) // 2)
        top = max(0, nh - th)
        right = left + tw
        bottom = top + th
        return scaled.crop((left, top, right, bottom))

    if mode == "letterbox":
        scale = min(tw / float(w), th / float(h))
        nw = max(1, int(round(w * scale)))
        nh = max(1, int(round(h * scale)))
        small = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (tw, th), (0, 0, 0))
        ox = (tw - nw) // 2
        oy = (th - nh) // 2
        canvas.paste(small, (ox, oy))
        return canvas

    if mode == "center":
        return _crop_resize_rgb_to_45(rgb)

    tgt = 4.0 / 5.0
    src_ratio = w / float(h)
    if src_ratio > tgt:
        new_w = max(1, int(round(h * tgt)))
        left = 0
        rgb = rgb.crop((left, 0, left + new_w, h))
    else:
        new_h = max(1, int(round(w / tgt)))
        top = max(0, h - new_h)
        rgb = rgb.crop((0, top, w, top + new_h))
    return rgb.resize((tw, th), Image.Resampling.LANCZOS)


def _run_cursor_prompt_notify_cmd(cmd: str) -> None:
    if not (cmd or "").strip():
        return
    try:
        import subprocess

        subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=os.name != "nt",
        )
    except Exception as e:
        print(f"CURSOR_PROMPT_READY_NOTIFY_CMD failed: {e}", flush=True)


def _wait_for_stable_inbound_image(inbound_abs: str, max_wait: float, poll: float) -> bool:
    """
    Return True if inbound exists and has stable non-zero size for two consecutive polls (avoids half-written files).
    """
    if max_wait <= 0:
        return os.path.isfile(inbound_abs)
    deadline = time.monotonic() + max_wait
    last_size: int | None = None
    stable = 0
    while time.monotonic() < deadline:
        if os.path.isfile(inbound_abs):
            try:
                sz = os.path.getsize(inbound_abs)
            except OSError:
                sz = 0
            if sz > 0 and last_size is not None and sz == last_size:
                stable += 1
                if stable >= 1:
                    return True
            else:
                stable = 0
                last_size = sz if sz > 0 else None
        time.sleep(poll)
    if not os.path.isfile(inbound_abs):
        return False
    try:
        return os.path.getsize(inbound_abs) > 0
    except OSError:
        return False


def _generate_post_image_cursor_tool_only(
    article,
    image_prompt,
    out_path: str,
    *,
    system_prompt=None,
    topic_theme=None,
    visual_style=None,
    video_scene_mode: bool = False,
):
    """
    No Z-Image, no PIL fallback: writes ``CURSOR_POST_IMAGE_PROMPT.txt``, expects PNG/JPEG at
    ``CURSOR_POST_IMAGE_INBOUND`` after you generate with the Cursor image tool.
    """
    print("Post image: Cursor image tool only (no Z-Image / no scripted image fallback).")
    inbound = (CURSOR_POST_IMAGE_INBOUND or "").strip() or os.path.join(_CONTENT_GEN_BASE, "cursor_post_image.png")
    prompt_path = (CURSOR_POST_IMAGE_PROMPT_PATH or "").strip() or os.path.join(
        _CONTENT_GEN_BASE, "CURSOR_POST_IMAGE_PROMPT.txt"
    )
    try:
        consume = bool(CURSOR_POST_IMAGE_CONSUME)
    except NameError:
        consume = True

    try:
        from config import CURSOR_USE_PIL_HEADLINE_OVERLAY as _use_pil_headline
    except ImportError:
        _use_pil_headline = True

    ip = image_prompt
    if ip is None:
        ip = generate_image_prompt_with_gemini(article, system_prompt=system_prompt, topic_theme=topic_theme, visual_style=visual_style)
    try:
        _cnp = COMPREHENSIVE_NEWS_IMAGE_PROMPT
    except NameError:
        _cnp = True
    if _cnp and article and not video_scene_mode:
        ip = _append_comprehensive_news_visual_directive_for_cursor(
            ip, article, pil_headline_overlay=_use_pil_headline
        )
    # When PIL headline overlay is on (default), Cursor image is scene-only; typography is fit to 4:5 in minimal_overlay.
    if article and not video_scene_mode and not _use_pil_headline:
        ip = (ip or "").strip() + _cursor_tool_mandatory_headline_suffix(article)

    title = (article.get("title") or article.get("headline") or "").strip()
    summary = (article.get("summary") or article.get("description") or "").strip()
    url = (article.get("url") or article.get("link") or "").strip()
    try:
        from config import CURSOR_HEADLINE_INSET_PCT as _ci
        _inset_b = max(5, min(15, int(_ci)))
    except Exception:
        _inset_b = 8
    if _use_pil_headline:
        cursor_instruction_block = (
            "**Scene only (no on-image headline):** photoreal 4:5 breaking-news still. Do **not** render headline text, "
            "lower-thirds, chyrons, tickers, or broadcast banners—the article title is typeset afterward with margins "
            "that match this aspect ratio.\n"
            "**ONE full-bleed photograph** edge to edge; no narrow center strip, blurred side pillars, or split panels.\n"
        )
    else:
        cursor_instruction_block = (
            "**ONE full-bleed photo across the entire canvas**—do **not** use a narrow center strip with blurred sides, "
            "mirrored wings, cinematic letterboxing, or split panels; those layouts clip headlines. "
            "**The Cursor image tool must produce ALL headline typography in this file**—polished lower-third or top banner, "
            "exact wording, high contrast, multi-line if needed. Nothing will add or replace headline text after export; "
            "this image is the single source of truth for the headline.\n"
            "**CRITICAL — NO EDGE BLEED:** Headline glyphs, shadows, and banner edges must stay **inside** the canvas with "
            f"**{_inset_b}%** empty margin on **left**, **right**, and **bottom** (see HEADLINE block for wrap rules). "
            "Half-cut letters at the border are unacceptable—use **more lines** and **smaller type** until everything fits. "
            "**The first letter of line 1 must not start at the image edge**—leave a full **inset band** of background visible "
            f"on the left (same on the right). Export at true **4:5** aspect so downstream crop does not trim text.\n"
        )
    bundle = (
        "=== Use the Cursor chat IMAGE tool to generate ONE still ===\n"
        "Strict **4:5 vertical portrait** frame (width:height = 4:5). US viral breaking-news style: photoreal scene "
        "that shows the CRUX of the story clearly (who, what, stakes, setting).\n"
        f"{cursor_instruction_block}"
        "No fake network logos; no watermarks. Save/export as PNG or JPEG.\n\n"
        f"=== Save the file to this exact path (overwrite if needed) ===\n{os.path.abspath(inbound)}\n\n"
        "=== Article ===\n"
        f"Title: {title}\nURL: {url}\nSummary: {summary}\n\n"
        "=== Image prompt (paste into Cursor image tool) ===\n"
        f"{(ip or '').strip()}\n"
    )
    try:
        pdir = os.path.dirname(os.path.abspath(prompt_path))
        if pdir:
            os.makedirs(pdir, exist_ok=True)
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(bundle)
        print(f"Wrote operator prompt: {os.path.abspath(prompt_path)}")
    except OSError as e:
        print(f"Could not write prompt file: {e}")

    try:
        from config import CURSOR_PROMPT_READY_NOTIFY_CMD as _notify_cmd
    except ImportError:
        _notify_cmd = ""
    _run_cursor_prompt_notify_cmd(_notify_cmd)

    inbound_abs = os.path.abspath(inbound)
    try:
        from config import (
            CURSOR_INBOUND_MAX_WAIT_SECONDS as _max_wait,
            CURSOR_INBOUND_POLL_INTERVAL_SECONDS as _poll_iv,
        )
    except ImportError:
        _max_wait = 0.0
        _poll_iv = 2.0
    if not os.path.isfile(inbound_abs) and float(_max_wait) > 0:
        print(
            f"\nWaiting up to {float(_max_wait):.0f}s for inbound image (Cursor tool → save to):\n  {inbound_abs}\n",
            flush=True,
        )
        _wait_for_stable_inbound_image(inbound_abs, float(_max_wait), float(_poll_iv))

    if not os.path.isfile(inbound_abs):
        print(
            "\nNo inbound image yet. Generate with the Cursor image tool, then save to:\n"
            f"  {inbound_abs}\n"
            "Re-run the posting step when the file exists. No diffusion fallback will run.\n"
            "Tip: set CURSOR_INBOUND_MAX_WAIT_SECONDS=600 so run_continuous_image_posts.py waits inside each slot.\n",
            flush=True,
        )
        return None

    try:
        from PIL import Image

        with Image.open(inbound_abs) as im:
            im.verify()
    except Exception as e:
        print(f"Inbound file is not a valid image: {inbound_abs} ({e})")
        return None

    out_abs = os.path.abspath(out_path)
    odir = os.path.dirname(out_abs)
    if odir:
        os.makedirs(odir, exist_ok=True)
    try:
        from PIL import Image

        with Image.open(inbound_abs) as im:
            rgb = _crop_resize_rgb_to_45_cursor_inbound(im.convert("RGB"))
            tw, th = get_post_image_dimensions_45()
            try:
                from config import CURSOR_INBOUND_CROP_MODE as _cm
            except Exception:
                _cm = "cover"
            print(f"Post image normalized to 4:5 vertical: {tw}x{th}px (inbound crop: {_cm})")
            ext = os.path.splitext(out_abs)[1].lower()
            if ext in (".jpg", ".jpeg"):
                rgb.save(out_abs, "JPEG", quality=95, optimize=True)
            else:
                rgb.save(out_abs, "PNG", optimize=True)
    except Exception as e:
        print(f"Could not copy inbound image to output path: {e}")
        return None

    if consume:
        try:
            os.remove(inbound_abs)
            print(f"Removed inbound (consumed): {inbound_abs}")
        except OSError as e:
            print(f"Note: could not remove inbound file: {e}")

    return _apply_post_image_overlays_and_label(out_abs, article, video_scene_mode=video_scene_mode)


def generate_post_image_fallback(
    article,
    image_prompt=None,
    output_path=None,
    system_prompt=None,
    topic_theme=None,
    visual_style=None,
    *,
    video_scene_mode=False,
):
    """Post image: **Cursor chat image tool only** — writes prompt bundle, waits for inbound file. No Z-Image, no placeholders."""
    out_path = output_path or POST_IMAGE_PATH
    return _generate_post_image_cursor_tool_only(
        article,
        image_prompt,
        out_path,
        system_prompt=system_prompt,
        topic_theme=topic_theme,
        visual_style=visual_style,
        video_scene_mode=video_scene_mode,
    )


def _print_cuda_setup_help():
    """Explain why torch may not see the GPU and how to install CUDA PyTorch."""
    print("=" * 60)
    print("GPU: PyTorch does not see CUDA (torch.cuda.is_available() is False).")
    print("Fix (Windows, use your project venv):")
    print("  1. In .env remove IMGEN_FEB_DEVICE=cpu if you want the NVIDIA GPU.")
    print("  2. Install/update NVIDIA drivers from nvidia.com.")
    print("  3. Install PyTorch built with CUDA (not the CPU-only wheel):")
    print('       pip uninstall torch torchvision -y')
    print('       pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124')
    print("     (Use cu121/cu118 from pytorch.org if your driver needs an older CUDA.)")
    print("  4. Run: python check_gpu.py")
    print("GPU + CPU together: IMGEN_FEB_DEVICE=cuda and IMGEN_FEB_USE_CPU_OFFLOAD=True")
    print("  (CPU offload keeps inactive layers on RAM; active compute on GPU.)")
    print("New RTX 50 / Blackwell: install nightly torch in .venv — install_nightly_torch_venv.bat ; check_gpu.py must pass kernel smoke.")
    print("  after installing a PyTorch nightly that supports your GPU (or risk native crash).")
    print("=" * 60)


def generate_image_with_imgen_feb(image_prompt, output_path=None):
    """Z-Image-Turbo via Hugging Face diffusers. If ``Z_IMAGE_LOCAL_DIFFUSERS_ONLY`` (default True): only ``runpod_image.py`` — no ``imgen_feb`` path or backend fallback."""
    image_path = output_path or POST_IMAGE_PATH
    if USE_SENSATIONAL_BREAKING_TEMPLATE:
        width, height = get_post_image_dimensions_45()
    else:
        width = height = IMGEN_FEB_SIZE
    # Ensure image has no embedded text/headline — only one headline, inside the overlay box
    _NO_TEXT_SUFFIX = " Do not draw or render any text, words, headlines, titles, magazine headlines, or letters anywhere in the image. No magazine-style text. Visual scene and objects only. The headline is added separately."
    _is_inst = False
    try:
        from config import IMAGE_VISUAL_MODE

        _is_inst = IMAGE_VISUAL_MODE == "institutional"
    except ImportError:
        pass
    _INSTITUTIONAL_IMG_SUFFIX = (
        " Deep navy and slate palette, subtle film grain, thin glowing accent lines, sleek minimalist charts, "
        "abstract structural shifts and liquidity geometry, institutional-grade terminal UI, calculated professional mood, "
        "no legible text, no logos, no watermarks, no stock-photo people."
    )
    prompt_text = (image_prompt or "").strip()
    if _is_inst:
        if _INSTITUTIONAL_IMG_SUFFIX.strip().lower() not in prompt_text.lower():
            prompt_text = prompt_text + _INSTITUTIONAL_IMG_SUFFIX
    else:
        if prompt_text and "vivid" not in prompt_text.lower():
            prompt_text = prompt_text + " Vivid, saturated colors; lively and eye-catching palette."
    if prompt_text and _NO_TEXT_SUFFIX.strip().lower() not in prompt_text.lower():
        prompt_text = prompt_text + _NO_TEXT_SUFFIX
    # Built-in diffusers module (runpod_image.py) supports negative_prompt; append institutional terms when mode is on
    _builtin_diffusers_negative_prompt = None
    if _is_inst:
        _builtin_diffusers_negative_prompt = (
            "text, words, letters, headline, title, writing, caption, typography, sign, watermark, label, "
            "text overlay, magazine cover, magazine headline, yellow text, large text on image, bold text overlay, "
            "newspaper headline style, stock photo, businessman, businesswoman, man holding head, hands on face, "
            "suit handshake, cheesy corporate, bright saturated cartoon, readable text, cluttered office people, "
            "photorealistic faces, portrait photography, office cubicle crowd"
        )

    device = (IMGEN_FEB_DEVICE or "cuda").strip().lower() if isinstance(IMGEN_FEB_DEVICE, str) else "cuda"
    use_offload = bool(IMGEN_FEB_USE_CPU_OFFLOAD) if IMGEN_FEB_USE_CPU_OFFLOAD is not None else True
    if device == "cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                _print_cuda_setup_help()
                if not IMGEN_ALLOW_CPU_FALLBACK:
                    print("IMGEN_ALLOW_CPU_FALLBACK=false — skipping image gen until CUDA works.")
                    return None
                print("Falling back to CPU (slow). Set IMGEN_ALLOW_CPU_FALLBACK=false to require GPU.")
                device = "cpu"
                use_offload = False
        except Exception:
            _print_cuda_setup_help()
            if not IMGEN_ALLOW_CPU_FALLBACK:
                return None
            device = "cpu"
            use_offload = False

    def _run_local_diffusers_zimage(negative_prompt=None):
        """Local Hugging Face diffusers path (file: runpod_image.py — name is legacy)."""
        clear_after = bool(IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE) if IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE is not None else False
        from runpod_image import generate_image as runpod_generate
        _steps = int(IMGEN_FEB_INFERENCE_STEPS) if IMGEN_FEB_INFERENCE_STEPS else 8
        _kw = dict(
            prompt=prompt_text,
            output_path=image_path,
            height=height,
            width=width,
            num_inference_steps=max(1, min(50, _steps)),
            device=device,
            use_cpu_offload_from_start=use_offload if device == "cuda" else False,
            clear_pipeline_after_generate=clear_after if device == "cuda" else False,
        )
        if negative_prompt is not None:
            _kw["negative_prompt"] = negative_prompt
        return runpod_generate(**_kw)

    def _finish_local_zimage_ok(result):
        if result:
            print(f"Image saved: {os.path.abspath(image_path)}")
            try:
                import gc
                gc.collect()
                if device == "cuda":
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
            except Exception:
                pass
        return image_path if result else None

    if Z_IMAGE_LOCAL_DIFFUSERS_ONLY:
        loc = "RunPod pod" if os.environ.get("RUNPOD") else "local"
        print(f"Z-Image-Turbo ({loc}): runpod_image.py only — no imgen_feb or alternate backends.")
        try:
            result = _run_local_diffusers_zimage(negative_prompt=_builtin_diffusers_negative_prompt)
            return _finish_local_zimage_ok(result)
        except Exception as e:
            print(f"Z-Image-Turbo (runpod_image.py) error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # RunPod in-pod: use diffusers-only module (no imgen_feb package)
    if os.environ.get("RUNPOD"):
        print("Generating image with Z-Image-Turbo (RunPod/diffusers)...")
        try:
            result = _run_local_diffusers_zimage(negative_prompt=_builtin_diffusers_negative_prompt)
            return _finish_local_zimage_ok(result)
        except Exception as e:
            print(f"RunPod pod image error: {e}")
            return None

    # Local but imgen_feb package not installed: use built-in diffusers module (runpod_image.py)
    if not IMGEN_FEB_AVAILABLE:
        print("Generating image with Z-Image-Turbo (local diffusers — imgen_feb not installed)...")
        try:
            result = _run_local_diffusers_zimage(negative_prompt=_builtin_diffusers_negative_prompt)
            return _finish_local_zimage_ok(result)
        except Exception as e:
            print(f"Built-in diffusers image error: {e}")
        return None

    # Prefer local built-in diffusers first (clearer env: IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST; legacy: IMGEN_PREFER_RUNPOD_IMAGE_LOCAL)
    _prefer_default = "1"
    _pref = os.environ.get("IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST")
    if _pref is None or str(_pref).strip() == "":
        _pref = os.environ.get("IMGEN_PREFER_RUNPOD_IMAGE_LOCAL", _prefer_default)
    _prefer_builtin_diffusers_first = str(_pref).strip().lower() not in ("0", "false", "no", "off")
    if os.name == "nt" and _prefer_builtin_diffusers_first:
        print("Windows detected: trying local Z-Image (Hugging Face diffusers) before imgen_feb...")
        try:
            result = _run_local_diffusers_zimage(negative_prompt=_builtin_diffusers_negative_prompt)
            if result:
                return _finish_local_zimage_ok(result)
            print("Built-in diffusers path did not return an image; falling back to imgen_feb...")
        except Exception as e:
            print(f"Built-in diffusers preflight failed: {e}; falling back to imgen_feb...")

    print("Generating image with imgen_feb (Z-Image-Turbo)...")
    try:
        result = None
        try:
            clear_after = bool(IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE) if IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE is not None else False
            # cuda: None = auto (VRAM vs IMGEN_OFFLOAD_VRAM_THRESHOLD_GB in imgen_feb); True = always offload; False = always full-GPU
            if device == "cuda":
                if not IMGEN_FEB_USE_CPU_OFFLOAD:
                    _offload_arg = False
                elif os.environ.get("IMGEN_FORCE_CPU_OFFLOAD", "").strip().lower() in ("1", "true", "yes", "on"):
                    _offload_arg = True
                else:
                    _offload_arg = None
            else:
                _offload_arg = None
            _steps = int(IMGEN_FEB_INFERENCE_STEPS) if IMGEN_FEB_INFERENCE_STEPS else 8
            result = imgen_feb.generate_image(
                prompt=prompt_text,
                output_path=image_path,
                height=height,
                width=width,
                num_inference_steps=_steps,
                device=device,
                use_cpu_offload_from_start=_offload_arg,
                clear_pipeline_after_generate=clear_after if device == "cuda" else False,
            )
        except Exception as gpu_err:
            err_msg = str(gpu_err).lower()
            if device == "cuda" and ("cuda" in err_msg or "gpu" in err_msg or "memory" in err_msg or "500" in err_msg):
                print(f"GPU error (fallback to CPU): {gpu_err}")
                try:
                    import gc
                    import torch

                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                result = imgen_feb.generate_image(
                    prompt=prompt_text,
                    output_path=image_path,
                    height=height,
                    width=width,
                    device="cpu",
                    use_cpu_offload_from_start=None,
                    clear_pipeline_after_generate=False,
                )
            else:
                raise
        if result:
            print(f"Image saved: {os.path.abspath(image_path)}")
        # Free memory immediately after generation (avoids GPU/CPU buildup over many cycles)
        try:
            import gc
            gc.collect()
            if device == "cuda":
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except Exception:
            pass
        return image_path if result else None
    except Exception as e:
        print(f"Error with imgen_feb: {e}")
        # Fallback: local diffusers module (runpod_image.py)
        print("Falling back to local Z-Image (Hugging Face diffusers)...")
        try:
            result = _run_local_diffusers_zimage(negative_prompt=_builtin_diffusers_negative_prompt)
            if result:
                return _finish_local_zimage_ok(result)
            return None
        except Exception as e2:
            print(f"Fallback image error: {e2}")
        return None

def generate_image_with_ollama(image_prompt):
    """Generate image via Ollama (e.g. x/z-image-turbo). Open-source, local."""
    if not USE_OLLAMA:
        return None
    try:
        from ollama_client import ollama_available, ollama_generate_image
        if not ollama_available():
            return None
        path = ollama_generate_image(image_prompt, output_path=POST_IMAGE_PATH)
        return path
    except Exception as e:
        print(f"Ollama image error: {e}")
        return None


def generate_image_with_imagen(image_prompt, output_path=None, safer_retry=False):
    """Image generation: only imgen_feb (Z-Image-Turbo) or local diffusers (`runpod_image.py`). No Ollama, cloud, or fallback."""
    print("Generating image with imgen_feb (Z-Image-Turbo) only...")
    if safer_retry:
        print("[RETRY] Safer image retry enabled for this attempt.")
    if not USE_IMGEN_FEB or not USE_ONLY_IMGEN_FEB:
        print("ERROR: Config requires only imgen_feb. Set USE_IMGEN_FEB=True and USE_ONLY_IMGEN_FEB=True in config.py")
        return None
    # When imgen_feb is not installed, generate_image_with_imgen_feb uses local diffusers (runpod_image.py)
    path = generate_image_with_imgen_feb(image_prompt, output_path=output_path)
    if not path:
        print("imgen_feb failed. No other backends used (imgen_feb only).")
    return path

def generate_video_with_veo3(video_prompt, duration_seconds: int = 20, aspect_ratio: str = "9:16", resolution: str = "1080p"):
    """Use Veo 3 to generate 8-second professional videos"""
    print("Generating 8-second video with Veo 3...")
    
    try:
        # Use the correct Google GenAI client for Veo 3
        import time
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Generate video using Veo 3
        # Retry with simple backoff on quota errors
        attempts = 0
        last_exc = None
        while attempts < 3:
            try:
                operation = client.models.generate_videos(
                    model="veo-3.0-generate-preview",
                    prompt=f"Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Resolution: {resolution}. " + video_prompt,
                    config=types.GenerateVideosConfig(
                        negative_prompt="blurry, low quality, distorted",
                    ),
                )
                break
            except Exception as e:
                last_exc = e
                attempts += 1
                import time as _t
                _t.sleep(8 * attempts)
        if attempts == 3 and last_exc:
            raise last_exc
        
        print("Video generation started, waiting for completion...")
        
        # Wait for the video to be generated
        while not operation.done:
            print("Generating video... (this may take 2-3 minutes)")
            time.sleep(20)
            operation = client.operations.get(operation)
        
        # Get the generated video
        if operation.result and operation.result.generated_videos:
            generated_video = operation.result.generated_videos[0]
            
            # Download and save the video
            video_path = "post_video.mp4"
            client.files.download(file=generated_video.video)
            generated_video.video.save(video_path)
            
            print(f"SUCCESS: Veo 3 video saved as {video_path}")
            return video_path
        else:
            print("No video generated by Veo 3")
            return None
        
    except Exception as e:
        print(f"Error with Veo 3: {e}")
        return None

def generate_image_with_imagen_vertex(image_prompt):
    """Use Vertex AI Imagen to generate the actual image (fallback)"""
    print("Generating image with Vertex AI Imagen...")
    
    if not VERTEX_AI_AVAILABLE:
        print("Vertex AI not available, using Gemini fallback")
        return generate_image_with_gemini(image_prompt)
    
    try:
        # Initialize Vertex AI
        aiplatform.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        
        # Import Imagen model
        from vertexai.preview.vision_models import ImageGenerationModel
        
        # Initialize Imagen model
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Generate image
        images = model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
            aspect_ratio=IMAGE_ASPECT_RATIO,
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        
        # Save image (AI label added once in generate_post_image_fallback)
        image_path = POST_IMAGE_PATH
        images[0].save(image_path)
        print(f"Image saved: {os.path.abspath(image_path)}")
        return image_path
        
    except Exception as e:
        print(f"Error with Vertex AI Imagen: {e}")
        return None

def generate_image_with_gemini(image_prompt):
    """Legacy hook — post images are Cursor-only; no API or PIL substitutes."""
    print("Scripted/API image generation disabled (project policy: Cursor image tool only for post stills).")
    return None


def create_fallback_image(article_or_prompt, output_path=None):
    """PIL placeholder images are permanently disabled (Cursor image tool only for post art)."""
    print("PIL placeholder images are disabled (project policy: no fallbacks — use the Cursor image tool).")
    return None

def generate_image_with_imagen4(article_or_prompt):
    """
    Generate an image using Imagen 4 via Gemini API.
    Accepts either an article dict (title, description) or a prompt string.
    """
    print("Generating image with Imagen 4...")
    
    try:
        if isinstance(article_or_prompt, str):
            image_prompt = article_or_prompt
        else:
            article = article_or_prompt
            image_prompt = f"""
        Create a professional, high-quality news image for this breaking news story:
        
        Title: {article['title']}
        Description: {article['description']}
        
        Requirements:
        - Professional news photography style
        - High quality, 16:9 aspect ratio
        - Relevant to the news story content
        - Professional lighting and composition
        - News-worthy visual elements
        - Clear, impactful imagery
        """
        
        # Use Imagen 4 model with predict method (requires Gemini/Vertex)
        g = _genai()
        model = g.GenerativeModel('imagen-4.0-generate-001')
        response = model.predict(image_prompt)
        
        # Save image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f"imagen4_post_{timestamp}.jpg"
        
        # Save the actual generated image
        if hasattr(response, 'parts') and response.parts:
            # Extract the image data from the response
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Save the actual generated image
                    with open(image_filename, 'wb') as f:
                        f.write(part.inline_data.data)
                    print(f"Actual AI-generated image saved: {image_filename}")
                    return image_filename
        
        print("Imagen 4 returned no image data; no PIL fallback (Cursor-only policy for post stills).")
        return None
        
    except Exception as e:
        print(f"Error generating image with Imagen 4: {e}")
        return None

def generate_image_with_gemini_from_article(article):
    """Legacy hook — no placeholder images."""
    print("Placeholder from article disabled (project policy: Cursor image tool only).")
    return None
