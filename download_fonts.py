#!/usr/bin/env python3
"""
Download Noto Sans (Black, Bold, Regular) into fonts/ so typography matches locally and on RunPod.
Run once locally, then include the fonts/ folder in your RunPod deploy for identical headline/text rendering.
Uses notofonts/noto-fonts (static hinted TTF); fallback: jsDelivr mirror of google/fonts.
"""
import os

# notofonts/noto-fonts has static Black, Bold, Regular (hinted TTF)
NOTOFONTS_RAW = "https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSans"
NOTO_SANS_URLS = {
    "black": [f"{NOTOFONTS_RAW}/NotoSans-Black.ttf"],
    "bold": [f"{NOTOFONTS_RAW}/NotoSans-Bold.ttf"],
    "regular": [f"{NOTOFONTS_RAW}/NotoSans-Regular.ttf"],
}
# Fallbacks (jsDelivr mirror of google/fonts ofl/notosans - may 403 in some environments)
for w in ("black", "bold", "regular"):
    NOTO_SANS_URLS[w].append(f"https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosans/NotoSans-{w.capitalize()}.ttf")

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    try:
        import requests
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"})
    except ImportError:
        session = None
    for weight, urls in NOTO_SANS_URLS.items():
        fname = f"NotoSans-{weight.capitalize()}.ttf"
        path = os.path.join(fonts_dir, fname)
        if os.path.isfile(path) and os.path.getsize(path) > 10000:
            print(f"OK (already present): {fname}")
            continue
        done = False
        for url in urls:
            try:
                if session:
                    r = session.get(url, timeout=20)
                    if r.status_code == 200 and len(r.content) > 10000:
                        with open(path, "wb") as f:
                            f.write(r.content)
                        print(f"OK (downloaded): {fname}")
                        done = True
                        break
                else:
                    import urllib.request
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Python)"})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        data = resp.read()
                    if len(data) > 10000:
                        with open(path, "wb") as f:
                            f.write(data)
                        print(f"OK (downloaded): {fname}")
                        done = True
                        break
            except Exception:
                continue
        if not done:
            print(f"FAIL: {fname} (tried {len(urls)} URL(s))")
    print("Done. Use fonts/ in your RunPod deploy for same typography as local.")

if __name__ == "__main__":
    main()
