from pathlib import Path
from typing import Iterator, Dict, Optional, List

from .facebook_poster import FacebookPoster


SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif"}


def _iter_images(root: str, patterns: Optional[List[str]] = None) -> Iterator[Path]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(root)
    if patterns:
        for pat in patterns:
            yield from (p for p in base.rglob(pat) if p.suffix.lower() in SUPPORTED_EXTS)
    else:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                yield p


def _read_sidecar_text(path: Path) -> Optional[str]:
    txt = path.with_suffix(".txt")
    if txt.exists():
        try:
            return txt.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


def determine_caption(path: Path, source: str) -> Optional[str]:
    s = source.lower()
    if s == "none":
        return None
    if s == "filename":
        return path.stem.replace("_", " ").replace("-", " ").strip()
    if s == "txt":
        return _read_sidecar_text(path)
    # default
    return None


def post_from_folder(
    poster: FacebookPoster,
    directory: str,
    *,
    caption_source: str = "filename",  # filename | txt | none
    patterns: Optional[List[str]] = None,
    limit: Optional[int] = None,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
) -> list:
    results = []
    count = 0
    for img in _iter_images(directory, patterns):
        caption = determine_caption(img, caption_source)
        if prefix:
            caption = f"{prefix}{(' ' + caption) if caption else ''}".strip()
        if suffix:
            caption = f"{(caption + ' ') if caption else ''}{suffix}".strip()
        results.append(poster.post_image_from_path(str(img), caption))
        count += 1
        if limit is not None and count >= limit:
            break
    return results



