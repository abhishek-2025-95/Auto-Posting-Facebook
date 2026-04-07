#!/usr/bin/env python3
"""
Fetch the last 50 Facebook page posts and report duplicates (same or very similar message).
Run from project root: python check_duplicate_posts.py
"""
import re
import sys
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from facebook_api import get_recent_posts

LIMIT = 50


def _normalize(msg):
    """Normalize message for comparison: strip, collapse whitespace, single line."""
    if not msg or not isinstance(msg, str):
        return ""
    s = " ".join(msg.split()).strip()
    return s


def _normalize_lower(msg):
    return _normalize(msg).lower()


def _similarity_words(a, b):
    """Jaccard-like word set similarity 0..1."""
    wa = set(re.findall(r"\w+", _normalize_lower(a)))
    wb = set(re.findall(r"\w+", _normalize_lower(b)))
    if not wa and not wb:
        return 1.0
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def main():
    print(f"Fetching last {LIMIT} page posts...")
    posts = get_recent_posts(limit=LIMIT)
    if not posts:
        print("No posts returned (check token and page ID).")
        return

    print(f"Retrieved {len(posts)} posts.\n")

    # Build normalized message -> list of (id, created_time, permalink, raw message)
    by_norm = {}
    for p in posts:
        msg = p.get("message") or ""
        raw = msg
        norm = _normalize(msg)
        key = _normalize_lower(msg) if norm else "__empty__"
        entry = (p.get("id"), p.get("created_time", ""), p.get("permalink_url", ""), raw)
        by_norm.setdefault(key, []).append(entry)

    # Exact duplicates (same normalized text)
    exact_dupes = [(k, v) for k, v in by_norm.items() if k != "__empty__" and len(v) > 1]
    if exact_dupes:
        print("=" * 60)
        print("EXACT DUPLICATES (same message text)")
        print("=" * 60)
        for key, group in exact_dupes:
            preview = (group[0][3] or "")[:80].replace("\n", " ")
            if len(preview) >= 80:
                preview += "..."
            print(f"\n  Message ({len(group)} posts): \"{preview}\"")
            for pid, ctime, permalink, _ in group:
                print(f"    - {ctime}  id={pid}")
                if permalink:
                    print(f"      {permalink}")
    else:
        print("No exact duplicates found.")

    # Near-duplicates: pairs with high word overlap
    post_list = [(p.get("id"), p.get("created_time", ""), p.get("permalink_url", ""), (p.get("message") or "")) for p in posts]
    near = []
    for i in range(len(post_list)):
        for j in range(i + 1, len(post_list)):
            a_id, a_time, a_url, a_msg = post_list[i]
            b_id, b_time, b_url, b_msg = post_list[j]
            if not a_msg.strip() or not b_msg.strip():
                continue
            if _normalize_lower(a_msg) == _normalize_lower(b_msg):
                continue  # already in exact dupes
            sim = _similarity_words(a_msg, b_msg)
            if sim >= 0.65:
                near.append((sim, a_msg, b_msg, a_time, b_time, a_id, b_id, a_url, b_url))

    if near:
        print("\n" + "=" * 60)
        print("NEAR-DUPLICATES (high message similarity)")
        print("=" * 60)
        for sim, a_msg, b_msg, a_time, b_time, a_id, b_id, a_url, b_url in sorted(near, key=lambda x: -x[0]):
            a_preview = (a_msg or "")[:60].replace("\n", " ")
            b_preview = (b_msg or "")[:60].replace("\n", " ")
            print(f"\n  Similarity: {sim:.0%}")
            print(f"    A: \"{a_preview}...\"  {a_time}  {a_id}")
            if a_url:
                print(f"       {a_url}")
            print(f"    B: \"{b_preview}...\"  {b_time}  {b_id}")
            if b_url:
                print(f"       {b_url}")
    else:
        print("\nNo near-duplicates found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
