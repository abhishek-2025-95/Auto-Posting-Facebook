"""Run this script to log in to Hugging Face (required for gated FLUX models)."""
from huggingface_hub import login

if __name__ == "__main__":
    print("Hugging Face login (needed for FLUX.1-schnell / FLUX.1-dev).")
    print()
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create a token (or use existing) with READ access.")
    print("3. Paste it below. Use a TOKEN, not your account password.")
    print("   (Paste only the token, no spaces before/after.)")
    print()
    try:
        login()
        print("Login successful.")
    except Exception as e:
        if "401" in str(e) or "Invalid" in str(e) or "Unauthorized" in str(e):
            print()
            print("Token was rejected. Check:")
            print("  - You used a token from https://huggingface.co/settings/tokens (not your password)")
            print("  - Token is valid and not revoked")
            print("  - No extra spaces or line breaks when pasting")
            print("  - Create a new token if unsure, then run this script again")
        raise
