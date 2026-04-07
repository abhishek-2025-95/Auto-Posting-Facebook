#!/bin/bash
# Run this once on a fresh RunPod to create dir, server file, venv, and install deps.
set -e
WORKDIR="/workspace/auto-posting-facebook"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Create runpod_image_server.py
cat > runpod_image_server.py << 'ENDOFFILE'
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

try:
    from flask import Flask, request, send_file
except ImportError:
    print("Install Flask: pip install flask")
    raise

app = Flask(__name__)

# Load model once at startup
_pipe = None

def get_pipe():
    global _pipe
    if _pipe is None:
        import torch
        from diffusers import DiffusionPipeline
        try:
            from diffusers.utils import logging as _dl
            _dl.disable_progress_bar()
        except Exception:
            pass
        model_id = os.environ.get("Z_IMAGE_TURBO_MODEL", "Tongyi-MAI/Z-Image-Turbo")
        print("Loading Z-Image-Turbo (" + model_id + ") on RunPod...")
        _pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            use_safetensors=True,
        )
        if torch.cuda.is_available():
            _pipe.enable_model_cpu_offload()
        else:
            _pipe = _pipe.to("cpu")
        print("Model loaded.")
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

        pipe = get_pipe()
        image = pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=8,
            guidance_scale=0.0,
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
    print(f"RunPod image server on 0.0.0.0:{port}. Set RUNPOD_IMAGE_API_URL on VPS to http://<this-pod-ip>:{port}")
    app.run(host="0.0.0.0", port=port, threaded=False)
ENDOFFILE

echo "Created runpod_image_server.py"

# Venv and install (ignore system blinker to avoid uninstall error)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --ignore-installed blinker flask torch diffusers transformers accelerate safetensors

echo ""
echo "Setup done. Run: cd $WORKDIR && source .venv/bin/activate && python runpod_image_server.py"
