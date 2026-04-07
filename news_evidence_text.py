"""
Optional helpers: extract numeric phrases from text, and strip subtitle digits not found in article fields.

Default manual video flow uses plain ``title`` + summary/description only (see ``build_manual_video_story_arc``).
Call ``sanitize_subtitle_numbers`` yourself if you need to vet a custom script against the article corpus.
"""
from __future__ import annotations

import re
from typing import Any, List, Mapping

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_QUANT_WORDS = re.compile(
    r"\b(percent|percentage|bps|basis\s+points?|billion|million|trillion|bn\b|mm\b|"
    r"quarter|q[1-4]|year-over-year|yoy|year on year)\b",
    re.IGNORECASE,
)
_CHIP_PATTERNS = [
    re.compile(r"\$[\d,.]+\s*(?:billion|million|bn|mm)?", re.IGNORECASE),
    re.compile(r"[\d,.]+%"),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:billion|million|trillion|bn|mm)\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"),
]

# Spans removed from subtitles if they do not appear in the article corpus (anti-hallucination).
_SUBTITLE_NUM_TOKEN_RE = re.compile(
    r"\$[\d,.]+(?:\s*(?:billion|million|trillion|bn|mm))?|"
    r"[\d,.]+%|"
    r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|"
    r"\b\d+(?:\.\d+)?\s*(?:billion|million|trillion|bn|mm)\b|"
    r"\b\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)


def _allowed_corpus(article: Mapping[str, Any]) -> str:
    """All article fields that count as source news for numeric grounding."""
    blobs: List[str] = []
    for key in ("title", "headline", "summary", "description", "content", "body"):
        v = article.get(key)
        if v and str(v).strip():
            blobs.append(str(v).strip())
    raw = article.get("key_stats") or article.get("key_metrics") or article.get("stats")
    if isinstance(raw, list):
        blobs.extend(str(x).strip() for x in raw if str(x).strip())
    elif isinstance(raw, str) and raw.strip():
        blobs.append(raw.strip())
    return "\n".join(blobs)


def _numeric_fragment_in_corpus(frag: str, corpus_lower: str) -> bool:
    f = frag.strip().lower()
    if not f:
        return True
    if f in corpus_lower:
        return True
    f2 = f.replace(",", "")
    c2 = corpus_lower.replace(",", "")
    if f2 in c2:
        return True
    m_pct = re.match(r"^([\d,.]+)%$", f)
    if m_pct:
        n = m_pct.group(1).replace(",", "")
        if n and n in c2:
            return True
    m_money = re.match(r"^\$([\d,.]+)(?:\s*(billion|million|trillion|bn|mm))?$", f)
    if m_money:
        n = m_money.group(1).replace(",", "")
        if n and n in c2:
            return True
    fd = re.sub(r"[^\d.%$]", "", f)
    cd = re.sub(r"[^\d.%$]", "", c2)
    if fd and len(fd) >= 1 and fd in cd:
        return True
    return False


def _strip_empty_by_numbers_section(text: str) -> str:
    lines = text.split("\n")
    out: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("By the numbers"):
            start = len(out)
            out.append(lines[i])
            i += 1
            while i < len(lines) and not lines[i].strip():
                out.append(lines[i])
                i += 1
            bullet_marks = len(out)
            while i < len(lines) and lines[i].strip().startswith("•"):
                content = lines[i].split("•", 1)[-1].strip()
                if content:
                    out.append(lines[i])
                i += 1
            if len(out) == bullet_marks:
                out = out[:start]
            continue
        out.append(lines[i])
        i += 1
    text2 = "\n".join(out)
    text2 = re.sub(r"\n{3,}", "\n\n", text2)
    return text2.strip()


def sanitize_subtitle_numbers(subtitle: str, article: Mapping[str, Any]) -> str:
    """
    Drop numeric tokens from subtitle text unless the same token appears in the article corpus
    (title, headline, summary, description, body fields, and manual key_stats).
    """
    raw = (subtitle or "").strip()
    if not raw:
        return raw
    corpus = _allowed_corpus(article)
    corpus_lower = corpus.lower()
    if not corpus_lower.strip():
        return raw
    matches = list(_SUBTITLE_NUM_TOKEN_RE.finditer(raw))
    s = raw
    for m in sorted(matches, key=lambda x: x.start(), reverse=True):
        frag = m.group(0)
        if not _numeric_fragment_in_corpus(frag, corpus_lower):
            s = s[: m.start()] + s[m.end() :]
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = _strip_empty_by_numbers_section(s)
    return s.strip()


def _sentence_has_quantity(s: str) -> bool:
    if not s or len(s) < 8:
        return False
    if re.search(r"\d", s):
        return True
    return bool(_QUANT_WORDS.search(s))


def _split_sentences(text: str) -> List[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    chunks = _SENTENCE_SPLIT.split(text)
    return [c.strip() for c in chunks if len(c.strip()) > 12]


def extract_stat_sentences(title: str, body: str, *, max_sentences: int = 6) -> List[str]:
    blob = f"{title or ''}. {body or ''}".strip()
    seen: set[str] = set()
    out: List[str] = []
    for s in _split_sentences(blob):
        if not _sentence_has_quantity(s):
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_sentences:
            break
    return out


def extract_numeric_chips(text: str, *, max_chips: int = 8) -> List[str]:
    text = text or ""
    found: List[str] = []
    seen: set[str] = set()
    for pat in _CHIP_PATTERNS:
        for m in pat.finditer(text):
            chip = m.group(0).strip()
            if len(chip) < 2 or chip.lower() in seen:
                continue
            seen.add(chip.lower())
            found.append(chip)
            if len(found) >= max_chips:
                return found
    return found

