"""
Post-processing: remove text drawn by the image model so only the overlay headline shows.
Uses EasyOCR + OpenCV inpainting when available; falls back to OpenCV-only (bright/yellow region detection) if OCR not installed.
Only the top SCENE_FRACTION of the image is processed so we never inpaint the bottom (headline box) region.
"""
import os

# Only remove text from the top fraction of the image (scene). Bottom is where our headline box overlay goes.
SCENE_FRACTION = 0.72


def _inpaint_scene_region_only(img, mask, y_cut):
    """Inpaint only the part of mask that lies above y_cut; return inpainted image."""
    import cv2
    import numpy as np
    mask_top = np.zeros_like(mask)
    mask_top[0:y_cut, :] = mask[0:y_cut, :]
    if np.any(mask_top > 0):
        return cv2.inpaint(img, mask_top, 5, cv2.INPAINT_TELEA)
    return img


def remove_text_from_image(image_path):
    """
    Detect text in the image (scene region only, top SCENE_FRACTION) and inpaint over it.
    Tries: EasyOCR -> pytesseract -> OpenCV-only (bright/yellow regions). Bottom area left untouched.
    Returns True if inpainting was run and the file was updated, False otherwise.
    """
    if not image_path or not os.path.isfile(image_path):
        return False
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("Text removal skipped: opencv not installed. pip install opencv-python-headless")
        return False
    img = cv2.imread(image_path)
    if img is None:
        return False
    h, w = img.shape[:2]
    y_cut = int(h * SCENE_FRACTION)

    # 1) Try EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(["en"], gpu=os.environ.get("CUDA_VISIBLE_DEVICES") is not None)
        results = reader.readtext(image_path)
        if results:
            mask = np.zeros((h, w), dtype=np.uint8)
            for (bbox, _text, _conf) in results:
                pts = np.array(bbox, dtype=np.int32)
                if int(pts[:, 1].mean()) > y_cut:
                    continue
                pad = 4
                xmin = max(0, pts[:, 0].min() - pad)
                ymin = max(0, pts[:, 1].min() - pad)
                xmax = min(w, pts[:, 0].max() + pad)
                ymax = min(y_cut, pts[:, 1].max() + pad)
                mask[ymin:ymax, xmin:xmax] = 255
            if np.any(mask > 0):
                out = _inpaint_scene_region_only(img, mask, y_cut)
                cv2.imwrite(image_path, out)
                print("Removed text from image (EasyOCR) before overlay.")
                return True
    except ImportError:
        pass
    except Exception as e:
        print(f"Text removal (EasyOCR) failed: {e}")

    # 2) Try pytesseract
    try:
        import pytesseract
        d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        n = len(d.get("text", []))
        mask = np.zeros((h, w), dtype=np.uint8)
        for i in range(n):
            if not (d["text"][i] or "").strip():
                continue
            x, y, ww, hh = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
            if y + hh > y_cut:
                continue
            pad = 3
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w, x + ww + pad), min(y_cut, y + hh + pad)
            mask[y1:y2, x1:x2] = 255
        if np.any(mask > 0):
            out = _inpaint_scene_region_only(img, mask, y_cut)
            cv2.imwrite(image_path, out)
            print("Removed text from image (pytesseract) before overlay.")
            return True
    except ImportError:
        pass
    except Exception as e:
        print(f"Text removal (pytesseract) failed: {e}")

    # 3) OpenCV-only fallback: remove only small, text-like bright regions (no full-width bands).
    # Full-width band inpainting was causing severe distortion/fading; we only mask compact blobs.
    try:
        roi = img[0:y_cut, :]
        rh, rw = roi.shape[:2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        bright = cv2.threshold(v, 180, 255, cv2.THRESH_BINARY)[1]
        saturated = cv2.threshold(s, 80, 255, cv2.THRESH_BINARY)[1]
        yellow_white = cv2.bitwise_or(bright, saturated)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        yellow_white = cv2.dilate(yellow_white, kernel)
        contours, _ = cv2.findContours(yellow_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros((h, w), dtype=np.uint8)
        min_area = (rh * rw) * 0.0005
        max_fraction = 0.15  # never mask more than 15% of scene from this fallback
        total_mask_area = 0
        for c in contours:
            if cv2.contourArea(c) < min_area:
                continue
            x2, y2, w2, h2 = cv2.boundingRect(c)
            if h2 < 8 or w2 < 15:
                continue
            # Only mask regions that look like text: not full-width (max 60% of width), not huge
            if w2 > rw * 0.6 or h2 > rh * 0.25:
                continue
            total_mask_area += w2 * h2
            if total_mask_area > (rh * rw * max_fraction):
                break
            mask[y2:y2 + h2, x2:x2 + w2] = 255
        if np.any(mask > 0):
            out = _inpaint_scene_region_only(img, mask, y_cut)
            cv2.imwrite(image_path, out)
            print("Removed text from image (OpenCV fallback) before overlay.")
            return True
    except Exception as e:
        print(f"Text removal (OpenCV fallback) failed: {e}")

    return False
