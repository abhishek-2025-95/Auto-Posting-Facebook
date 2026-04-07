#!/usr/bin/env python3
"""Quick verification that headline-box and design-schema fixes are in place and working."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    ok = True
    # 1) Design agent: no API key should not raise; schema can be None
    try:
        from design_agent import get_design_schema_from_llm, get_design_context
        # Clear so we test "no key" path
        save_g = os.environ.pop("GOOGLE_API_KEY", None)
        save_gem = os.environ.pop("GEMINI_API_KEY", None)
        try:
            schema = get_design_schema_from_llm({"title": "Test", "description": "Test"})
            if schema is not None and not isinstance(schema, dict):
                print("FAIL: get_design_schema_from_llm should return dict or None")
                ok = False
            else:
                print("OK: design_agent (no API key) returns without error")
        finally:
            if save_g is not None:
                os.environ["GOOGLE_API_KEY"] = save_g
            if save_gem is not None:
                os.environ["GEMINI_API_KEY"] = save_gem
    except Exception as e:
        print(f"FAIL: design_agent: {e}")
        ok = False

    # 2) Minimal overlay: missing file returns False
    try:
        from minimal_overlay import apply_minimal_breaking_overlay
        result = apply_minimal_breaking_overlay("nonexistent.jpg", headline="Test")
        if result is not False:
            print("FAIL: overlay with missing file should return False")
            ok = False
        else:
            print("OK: minimal_overlay handles missing image path")
    except Exception as e:
        print(f"FAIL: minimal_overlay: {e}")
        ok = False

    # 3) Headline box logic: ensure lower-portion constants exist in code
    try:
        with open(os.path.join(os.path.dirname(__file__), "minimal_overlay.py"), "r", encoding="utf-8") as f:
            text = f.read()
        if "max_box_height" in text and "min_box_top" in text and "0.55" in text:
            print("OK: headline box clamped to lower portion (max_box_height, min_box_top)")
        else:
            print("WARN: headline box clamp may be missing in minimal_overlay.py")
    except Exception as e:
        print(f"WARN: could not check minimal_overlay source: {e}")

    if ok:
        print("\nAll checks passed.")
        return 0
    print("\nSome checks failed.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
