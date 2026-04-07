# Noto Sans fonts (for same typography locally and on RunPod)

Place these `.ttf` files in this folder so overlay headline/text matches everywhere:

- **NotoSans-Black.ttf**
- **NotoSans-Bold.ttf**
- **NotoSans-Regular.ttf**

## How to get them

1. **Run the download script** (if your network allows):
   ```bash
   python download_fonts.py
   ```

2. **Or download manually** from Google Fonts:
   - Open https://fonts.google.com/noto/specimen/Noto+Sans
   - Click "Download family" and unzip
   - Copy `NotoSans-Black.ttf`, `NotoSans-Bold.ttf`, `NotoSans-Regular.ttf` into this `fonts/` folder

3. **Or use system Noto** (e.g. on Linux): copy from `/usr/share/fonts/truetype/noto/` if present.

If this folder is empty, the app will try to download Noto on first use (design_utils) or fall back to system fonts (Arial/Segoe UI), which can look different on RunPod vs Windows.
