"""
Ollama client for text and image generation (open-source, local).
Use instead of Gemini for captions, image prompts, and optionally image generation.
Requires Ollama running locally: https://ollama.com (e.g. ollama serve).
When Ollama is shared by multiple projects, increase OLLAMA_TIMEOUT and OLLAMA_RETRIES in .env.
"""

import json
import base64
import os
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TEXT_MODEL = "llama3.2"
DEFAULT_IMAGE_MODEL = "x/z-image-turbo"
DEFAULT_TIMEOUT = 600  # 10 min when shared; captions/prompts can be slow
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 30


def _base_url():
    try:
        from config import OLLAMA_BASE_URL
        return OLLAMA_BASE_URL
    except ImportError:
        return os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)


def _timeout():
    try:
        from config import OLLAMA_TIMEOUT
        return int(OLLAMA_TIMEOUT)
    except (ImportError, TypeError, ValueError):
        return DEFAULT_TIMEOUT


def _retries():
    try:
        from config import OLLAMA_RETRIES
        return max(1, int(OLLAMA_RETRIES))
    except (ImportError, TypeError, ValueError):
        return DEFAULT_RETRIES


def _retry_delay():
    try:
        from config import OLLAMA_RETRY_DELAY
        return max(0, int(OLLAMA_RETRY_DELAY))
    except (ImportError, TypeError, ValueError):
        return DEFAULT_RETRY_DELAY


def ollama_available(base_url=None):
    """Check if Ollama is running and reachable."""
    if not REQUESTS_AVAILABLE:
        return False
    url = (base_url or _base_url()).rstrip("/")
    try:
        r = requests.get(f"{url}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def ollama_generate_text(prompt, model=None, base_url=None, stream=False, options=None):
    """
    Generate text using Ollama (for captions, image prompts, etc.).
    options: optional dict for Ollama (e.g. {"num_predict": 600} for longer captions).
    Returns the generated string or empty string on failure.
    """
    if not REQUESTS_AVAILABLE:
        print("Ollama: requests not installed")
        return ""
    try:
        from config import OLLAMA_TEXT_MODEL
        model = model or OLLAMA_TEXT_MODEL
    except ImportError:
        model = model or DEFAULT_TEXT_MODEL
    url = (base_url or _base_url()).rstrip("/") + "/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": stream}
    if options and isinstance(options, dict):
        payload["options"] = options
    timeout = _timeout()
    retries = _retries()
    retry_delay = _retry_delay()
    last_error = None
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = retry_delay * attempt
                print(f"Ollama busy or timed out, waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
            if stream:
                out = []
                with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            obj = json.loads(line)
                            if obj.get("response"):
                                out.append(obj["response"])
                            if obj.get("done"):
                                break
                return "".join(out).strip()
            else:
                r = requests.post(url, json=payload, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                return (data.get("response") or "").strip()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 503:
                if attempt < retries - 1:
                    print(f"Ollama queue full (503), will retry ({attempt + 1}/{retries}). Set OLLAMA_NUM_PARALLEL on the Ollama server for concurrent requests.")
                else:
                    print(f"Ollama queue full after {retries} tries. On the machine running Ollama, set OLLAMA_NUM_PARALLEL=4 (or higher) and restart Ollama.")
                last_error = e
            else:
                print(f"Ollama text generation error: {e}")
                return ""
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
            last_error = e
            if attempt < retries - 1:
                print(f"Ollama timed out ({timeout}s), will retry ({attempt + 1}/{retries})...")
            else:
                print(f"Ollama text generation timed out after {retries} tries. Set OLLAMA_TIMEOUT and OLLAMA_RETRIES in .env when shared by multiple projects.")
        except (requests.exceptions.ConnectionError, ConnectionResetError, OSError) as e:
            last_error = e
            if attempt < retries - 1:
                print(f"Ollama busy or unreachable ({e}), will retry ({attempt + 1}/{retries})...")
            else:
                print(f"Ollama unavailable after {retries} tries. Set OLLAMA_NUM_PARALLEL on the Ollama server so multiple projects can run at once.")
        except Exception as e:
            print(f"Ollama text generation error: {e}")
            return ""
    return ""


def ollama_generate_image(prompt, output_path="post_image.jpg", model=None, base_url=None):
    """
    Generate an image using Ollama (e.g. x/z-image-turbo or flux).
    Returns output_path if successful, None otherwise.
    """
    if not REQUESTS_AVAILABLE:
        return None
    try:
        from config import OLLAMA_IMAGE_MODEL
        model = model or OLLAMA_IMAGE_MODEL
    except ImportError:
        model = model or DEFAULT_IMAGE_MODEL
    url = (base_url or _base_url()).rstrip("/") + "/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    timeout = _timeout()
    retries = _retries()
    retry_delay = _retry_delay()
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = retry_delay * attempt
                print(f"Ollama image: busy or timed out, waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            # Some Ollama image models return image as base64 in response
            image_b64 = data.get("image") or data.get("data")
            if image_b64:
                raw = base64.b64decode(image_b64)
                with open(output_path, "wb") as f:
                    f.write(raw)
                return output_path
            # If no image in response, try images array (multipart)
            for img in data.get("images", []):
                if isinstance(img, str):
                    raw = base64.b64decode(img)
                    with open(output_path, "wb") as f:
                        f.write(raw)
                    return output_path
            return None
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
            if attempt < retries - 1:
                print(f"Ollama image timed out ({timeout}s), will retry ({attempt + 1}/{retries})...")
            else:
                print(f"Ollama image timed out after {retries} tries. Set OLLAMA_TIMEOUT/OLLAMA_RETRIES in .env.")
            continue
        except (requests.exceptions.ConnectionError, ConnectionResetError, OSError) as e:
            if attempt < retries - 1:
                print(f"Ollama image: busy or unreachable, will retry ({attempt + 1}/{retries})...")
            else:
                print(f"Ollama image unavailable after {retries} tries.")
            continue
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 503:
                if attempt < retries - 1:
                    print(f"Ollama image: queue full (503), will retry ({attempt + 1}/{retries}). Set OLLAMA_NUM_PARALLEL on Ollama server.")
                else:
                    print(f"Ollama image queue full after {retries} tries. On the machine running Ollama, set OLLAMA_NUM_PARALLEL=4 and restart Ollama.")
                continue
            if e.response is not None and e.response.status_code == 404:
                print("Ollama image generation not available (endpoint or image model not supported on this setup).")
            else:
                print(f"Ollama image generation error: {e}")
            return None
        except Exception as e:
            print(f"Ollama image generation error: {e}")
            return None
    return None
