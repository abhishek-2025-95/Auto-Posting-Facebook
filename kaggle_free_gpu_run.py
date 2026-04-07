#!/usr/bin/env python3
"""
Run one full post cycle on Kaggle's free GPU.
Upload this file to a Kaggle Notebook, enable GPU (Settings → Accelerator → GPU),
add Secrets (GEMINI_API_KEY, NEWS_API_KEY, PAGE_ACCESS_TOKEN, PAGE_ID), then run all cells.

Alternatively, copy the cells below into a new Kaggle notebook.
"""
# === CELL 1: Setup and secrets (run first) ===
import os
import sys
import requests
import json

# Kaggle Secrets: Add-ons → Secrets → create GEMINI_API_KEY, NEWS_API_KEY, PAGE_ACCESS_TOKEN, PAGE_ID
try:
    from kaggle_secrets import UserSecretsClient
    _s = UserSecretsClient()
    os.environ["GEMINI_API_KEY"] = _s.get_secret("GEMINI_API_KEY")
    os.environ["NEWS_API_KEY"] = _s.get_secret("NEWS_API_KEY")
    os.environ["PAGE_ACCESS_TOKEN"] = _s.get_secret("PAGE_ACCESS_TOKEN")
    os.environ["PAGE_ID"] = _s.get_secret("PAGE_ID")
except Exception as e:
    print("Kaggle Secrets not loaded (run on Kaggle with Secrets attached):", e)

# Install deps not in Kaggle base image
import subprocess
for pkg in ["google-generativeai", "python-dotenv"]:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=False)

import torch
print("GPU available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device:", torch.cuda.get_device_name(0))

# === CELL 2: Fetch one news article ===
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
article = None
if NEWS_API_KEY:
    try:
        r = requests.get(
            "https://newsdata.io/api/1/latest",
            params={"apikey": NEWS_API_KEY, "language": "en", "country": "us"},
            timeout=15,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            a = results[0]
            article = {
                "title": a.get("title") or a.get("title_full", "")[:200],
                "description": (a.get("description") or a.get("content") or "")[:500],
                "url": a.get("link") or a.get("url", ""),
                "source": a.get("source_id", "News"),
            }
            print("Article:", article["title"][:60], "...")
    except Exception as e:
        print("News fetch failed:", e)
if not article:
    article = {
        "title": "Markets Open Higher Amid Earnings Wave",
        "description": "Stocks rise as investors digest quarterly results and Fed outlook.",
        "url": "https://example.com",
        "source": "Sample",
    }
    print("Using sample article (set NEWS_API_KEY in Secrets for real news).")

# === CELL 3: Gemini caption + image prompt ===
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

def gemini_caption(art):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""You are a senior US news editor. Based on this article write a Facebook caption.
Title: {art['title']}
Description: {art['description']}
Requirements: Start with BREAKING: or JUST IN:. 180-250 words. End with 20-30 hashtags. No emojis. Return only the caption."""
    r = model.generate_content(prompt)
    return r.text.strip() if r and r.text else ""

def gemini_image_prompt(art):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""Create a single image generation prompt (one sentence, no quotes) for a photorealistic, dramatic news-style image about this headline. No text in the image. Professional, vivid.
Headline: {art['title']}"""
    r = model.generate_content(prompt)
    return (r.text.strip().strip('"') if r and r.text else "Professional news scene, dramatic lighting")[:500]

caption = gemini_caption(article)
image_prompt = gemini_image_prompt(article)
print("Caption length:", len(caption))
print("Image prompt:", image_prompt[:80], "...")

# === CELL 4: Generate image with Z-Image-Turbo on Kaggle GPU ===
from diffusers import DiffusionPipeline
import torch
import gc

device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = os.environ.get("Z_IMAGE_TURBO_MODEL", "Tongyi-MAI/Z-Image-Turbo")
print("Loading", model_id, "on", device, "...")
pipe = DiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    use_safetensors=True,
)
if device == "cuda":
    pipe.enable_model_cpu_offload()
else:
    pipe = pipe.to(device)

prompt = (image_prompt or "Professional news scene") + " Vivid, saturated colors; high quality."
out_path = "/kaggle/working/post_image.jpg"
# 1024x1280 portrait
image = pipe(
    prompt=prompt,
    height=1280,
    width=1024,
    num_inference_steps=8,
    guidance_scale=0.0,
).images[0]
image.save(out_path)
print("Saved:", out_path)
del pipe
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# === CELL 5: Simple headline overlay (PIL) ===
from PIL import Image, ImageDraw, ImageFont

img = Image.open(out_path).convert("RGB")
draw = ImageDraw.Draw(img)
w, h = img.size
# Dark bar bottom 25%
bar_h = int(h * 0.25)
draw.rectangle([0, h - bar_h, w, h], fill=(20, 30, 60))
# Headline text (first 10 words)
headline = " ".join((article.get("title") or "Breaking News")[:80].split()[:10])
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", min(48, w // 18))
except Exception:
    font = ImageFont.load_default()
# Center text in bar
bbox = draw.textbbox((0, 0), headline, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
x = (w - tw) // 2
y = h - bar_h + (bar_h - th) // 2
draw.text((x, y), headline, fill=(255, 255, 255), font=font)
img.save(out_path, quality=95)
print("Overlay applied.")

# === CELL 6: Post to Facebook ===
PAGE_ID = os.environ.get("PAGE_ID", "").strip()
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "").strip()
if not PAGE_ID or not PAGE_ACCESS_TOKEN:
    print("Set PAGE_ID and PAGE_ACCESS_TOKEN in Kaggle Secrets to post. Image saved to /kaggle/working/post_image.jpg")
else:
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    with open(out_path, "rb") as f:
        r = requests.post(url, files={"source": f}, data={"access_token": PAGE_ACCESS_TOKEN, "caption": caption[:63000], "published": "true"}, timeout=60)
    if r.ok:
        print("SUCCESS: Posted to Facebook.")
    else:
        print("Post failed:", r.status_code, r.text[:300])
