#!/usr/bin/env python3
"""
Image-generation-only server for RunPod. Run this on the RunPod GPU pod.
VPS runs the rest of the pipeline (news, caption, overlay, Facebook) and calls this API.

Usage on RunPod:
  pip install flask
  python runpod_image_server.py

Then from VPS set RUNPOD_IMAGE_API_URL=http://<RUNPOD_PUBLIC_IP>:5000
"""
import io
import gc
import os
import sys

def _log(msg):
    print(msg, flush=True)
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

try:
    from flask import Flask, request, send_file
except ImportError:
    _log("Install Flask: pip install flask")
    raise

app = Flask(__name__)

# Load model once at startup
_pipe = None
_load_error = None

def get_pipe():
    global _pipe, _load_error
    if _load_error:
        raise RuntimeError(_load_error)
    if _pipe is None:
        import torch
        from diffusers import DiffusionPipeline
        try:
            from diffusers.utils import logging as _dl
            _dl.disable_progress_bar()
        except Exception:
            pass
        model_id = os.environ.get("Z_IMAGE_TURBO_MODEL", "Tongyi-MAI/Z-Image-Turbo")
        _log(f"Loading Z-Image-Turbo ({model_id}) on RunPod...")
        try:
            try:
                from diffusers import ZImagePipeline
                _pipe = ZImagePipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    use_safetensors=True,
                    low_cpu_mem_usage=False,
                )
            except (ImportError, AttributeError):
                _pipe = DiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    use_safetensors=True,
                    trust_remote_code=True,
                )
            if torch.cuda.is_available():
                _pipe.enable_model_cpu_offload()
            else:
                _pipe = _pipe.to("cpu")
            _log("Model loaded.")
        except Exception as e:
            import traceback
            _load_error = str(e)
            _log("Model load FAILED: " + _load_error)
            _log(traceback.format_exc())
            raise
    return _pipe

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/generate", methods=["POST"])
def generate():
    """POST JSON: {"prompt": "...", "width": 768, "height": 960}. Returns image/jpeg."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return {"error": "missing prompt"}, 400
        width = int(data.get("width", 768))
        height = int(data.get("height", 960))
        if "vivid" not in prompt.lower():
            prompt = prompt + " Vivid, saturated colors; lively and eye-catching palette."
        _no_text = " Do not draw or render any text, words, headlines, titles, magazine headlines, or letters anywhere in the image. No magazine-style text. Visual scene and objects only. The headline is added separately."
        if _no_text.strip().lower() not in prompt.lower():
            prompt = prompt + _no_text
        negative_prompt = "text, words, letters, headline, title, writing, caption, typography, sign, watermark, label, text overlay, magazine cover, magazine headline, yellow text, large text on image, bold text overlay, newspaper headline style"
        guidance_scale = 3.5

        pipe = get_pipe()
        try:
            image = pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=8,
                guidance_scale=guidance_scale,
                negative_prompt=negative_prompt,
            ).images[0]
        except TypeError:
            image = pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=8,
                guidance_scale=guidance_scale,
            ).images[0]

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        return send_file(buf, mimetype="image/jpeg", as_attachment=False)
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    _log(f"RunPod image server on 0.0.0.0:{port}. Set RUNPOD_IMAGE_API_URL on VPS to http://<this-pod-ip>:{port}")
    # Load model at startup so first /generate does not timeout or OOM during load
    _log("Preloading model (may take 1-2 min; needs ~8GB+ GPU VRAM)...")
    try:
        get_pipe()
        _log("Model ready. Starting Flask.")
    except Exception as e:
        _log("Preload failed; Flask will start but /generate will return errors: " + str(e))
    app.run(host="0.0.0.0", port=port, threaded=False)
