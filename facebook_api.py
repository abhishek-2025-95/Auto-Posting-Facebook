# facebook_api.py - Post content to Facebook Page
import requests
import os
import time
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

# Meta Graph API rate limit: error code 4 (throttling), 17 (rate limit), or HTTP 429
RATE_LIMIT_RETRY_DELAYS = [60, 120, 300]  # seconds (exponential backoff)
RATE_LIMIT_MAX_RETRIES = len(RATE_LIMIT_RETRY_DELAYS)
# Retry on 5xx (Facebook server errors) - often transient
SERVER_ERROR_RETRY_DELAYS = [10, 30, 60]  # seconds
SERVER_ERROR_MAX_RETRIES = len(SERVER_ERROR_RETRY_DELAYS)
GRAPH_API_VERSION = "v21.0"  # use current supported version (v18 can return 500 in some cases)


def _is_rate_limit_response(response):
    """True if Meta API indicates throttling (code 4 or 17) or HTTP 429."""
    if response.status_code == 429:
        return True
    try:
        data = response.json()
        code = data.get("error", {}).get("code")
        return code in (4, 17)
    except Exception:
        return False


def _is_server_error_response(response):
    """True if Facebook returned 5xx (transient server error)."""
    return 500 <= response.status_code < 600


def _page_creds(page_id=None, page_access_token=None):
    """Resolve page ID and token: prefer passed-in, else config."""
    return (
        page_id or FACEBOOK_PAGE_ID,
        page_access_token or FACEBOOK_ACCESS_TOKEN,
    )

def post_to_facebook_page(caption, media_path, ai_label_already_applied=False, page_id=None, page_access_token=None):
    """
    Post image or video with caption to Facebook Page using Graph API.
    MANDATORY: Every image must have "AI Generated" label before upload. Set ai_label_already_applied=True
    when the pipeline already applied it (e.g. minimal overlay) to avoid opening the file again.
    Use page_id and page_access_token for multi-agent (one per page); omit to use config.
    """
    pid, token = _page_creds(page_id, page_access_token)
    print("Posting to Facebook...")
    
    try:
        # Check if file exists
        if not os.path.exists(media_path):
            print(f"Error: Media file {media_path} not found")
            return False
        
        # Determine if it's a video or image based on file extension
        file_extension = media_path.lower().split('.')[-1]
        is_video = file_extension in ['mp4', 'mov', 'avi', 'mkv']
        
        # MANDATORY: Apply "AI Generated" label to every image before posting (skip if already applied for memory efficiency)
        if not is_video and not ai_label_already_applied:
            try:
                from ai_label import add_ai_generated_label
                add_ai_generated_label(media_path)
            except Exception as e:
                print(f"WARNING: Could not add mandatory AI label: {e}")
        
        if is_video:
            url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{pid}/videos"
            file_key = 'source'
            data = {
                'access_token': token,
                'description': caption,
                'published': 'true'
            }
        else:
            url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{pid}/photos"
            file_key = 'source'
            data = {
                'access_token': token,
                'caption': caption,
                'published': 'true'
            }

        # Make the API request with rate-limit and 5xx retry
        result = None
        last_response = None
        max_attempts = max(RATE_LIMIT_MAX_RETRIES, SERVER_ERROR_MAX_RETRIES) + 1
        for attempt in range(max_attempts):
            with open(media_path, 'rb') as media_file:
                files = {file_key: media_file}
                response = requests.post(url, files=files, data=data)
            last_response = response
            if response.ok:
                result = response.json()
                break
            if _is_rate_limit_response(response) and attempt < RATE_LIMIT_MAX_RETRIES:
                delay = RATE_LIMIT_RETRY_DELAYS[attempt]
                print(f"Rate limit hit; retrying in {delay}s (attempt {attempt+1}/{RATE_LIMIT_MAX_RETRIES})")
                time.sleep(delay)
                continue
            if _is_server_error_response(response) and attempt < SERVER_ERROR_MAX_RETRIES:
                delay = SERVER_ERROR_RETRY_DELAYS[attempt]
                print(f"Facebook server error ({response.status_code}); retrying in {delay}s (attempt {attempt+1}/{SERVER_ERROR_MAX_RETRIES})...")
                time.sleep(delay)
                continue
            # No retry or out of retries: show error and raise
            try:
                err_body = response.text[:500] if response.text else ""
                if err_body:
                    print(f"Facebook API response: {err_body}")
            except Exception:
                pass
            response.raise_for_status()

        if result is None:
            if last_response is not None:
                try:
                    print(f"Facebook API response: {last_response.text[:500]}")
                except Exception:
                    pass
                last_response.raise_for_status()
            result = last_response.json() if last_response else {}

        if 'id' in result:
            post_id = result['id']
            print(f"SUCCESS: Post successful! Post ID: {post_id}")
            print(f"View post: https://www.facebook.com/{post_id}")
            return post_id
        else:
            print(f"FAILED: Post failed: {result}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"FAILED: Network error posting to Facebook: {e}")
        return False
    except FileNotFoundError:
        print(f"FAILED: Media file not found: {media_path}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error posting to Facebook: {e}")
        return False

def post_text_only(caption, page_id=None, page_access_token=None):
    """
    Post text-only content to Facebook Page (fallback if image fails).
    Use page_id and page_access_token for multi-agent; omit to use config.
    """
    pid, token = _page_creds(page_id, page_access_token)
    print("Posting text-only content to Facebook...")
    
    try:
        # Facebook Graph API endpoint for posting text
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{pid}/feed"
        
        # Parameters for the post
        data = {
            'access_token': token,
            'message': caption,
            'published': 'true'
        }

        result = None
        for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
            response = requests.post(url, data=data)
            if not _is_rate_limit_response(response):
                response.raise_for_status()
                result = response.json()
                break
            if attempt < RATE_LIMIT_MAX_RETRIES:
                delay = RATE_LIMIT_RETRY_DELAYS[attempt]
                print(f"Rate limit hit; retrying in {delay}s (attempt {attempt+1}/{RATE_LIMIT_MAX_RETRIES})")
                time.sleep(delay)
        if result is None:
            response.raise_for_status()
            result = response.json()
        
        if 'id' in result:
            post_id = result['id']
            print(f"SUCCESS: Text post successful! Post ID: {post_id}")
            print(f"View post: https://www.facebook.com/{post_id}")
            return True
        else:
            print(f"FAILED: Text post failed: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Network error posting text to Facebook: {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error posting text to Facebook: {e}")
        return False

def test_facebook_connection(page_id=None, page_access_token=None):
    """
    Test Facebook API connection and permissions.
    Use page_id and page_access_token for multi-agent; omit to use config.
    """
    pid, token = _page_creds(page_id, page_access_token)
    print("Testing Facebook API connection...")
    if not token or not str(token).strip():
        print("FAILED: FACEBOOK_ACCESS_TOKEN (or PAGE_ACCESS_TOKEN) is empty.")
        print("  Set it in your .env file, e.g.:")
        print("    PAGE_ACCESS_TOKEN=EAAB...your_page_access_token")
        print("    PAGE_ID=758737463999000")
        print("  Or set FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env")
        return False
    if not pid or not str(pid).strip():
        print("FAILED: FACEBOOK_PAGE_ID (or PAGE_ID) is empty.")
        print("  Set PAGE_ID=your_page_id in .env")
        return False
    try:
        # Test API access
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{pid}"
        params = {
            'access_token': token,
            'fields': 'id,name,access_token'
        }

        result = None
        for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
            response = requests.get(url, params=params)
            if not _is_rate_limit_response(response):
                response.raise_for_status()
                result = response.json()
                break
            if attempt < RATE_LIMIT_MAX_RETRIES:
                delay = RATE_LIMIT_RETRY_DELAYS[attempt]
                print(f"Rate limit hit; retrying in {delay}s (attempt {attempt+1}/{RATE_LIMIT_MAX_RETRIES})")
                time.sleep(delay)
        if result is None:
            response.raise_for_status()
            result = response.json()

        print(f"SUCCESS: Facebook API connection successful!")
        print(f"Page: {result.get('name', 'Unknown')}")
        print(f"Page ID: {result.get('id', 'Unknown')}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Facebook API connection failed: {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error testing Facebook connection: {e}")
        return False


def debug_access_token(input_token=None, page_access_token=None):
    """
    Inspect a Page (or User) access token via Graph API debug_token.
    Requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment (.env).
    Returns the 'data' dict (is_valid, scopes, type, expires_at, …) or None if skipped, or dict with 'error' key.
    """
    try:
        import os
        app_id = (os.environ.get("FACEBOOK_APP_ID") or os.environ.get("META_APP_ID") or "").strip()
        app_secret = (os.environ.get("FACEBOOK_APP_SECRET") or os.environ.get("META_APP_SECRET") or "").strip()
        if not app_id or not app_secret:
            return None
        token = (input_token or page_access_token or FACEBOOK_ACCESS_TOKEN or "").strip()
        if not token:
            return {"error": "No access token provided"}
        app_access = f"{app_id}|{app_secret}"
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/debug_token"
        response = requests.get(
            url,
            params={"input_token": token, "access_token": app_access},
            timeout=30,
        )
        if not response.ok:
            return {"error": response.text[:800], "http_status": response.status_code}
        body = response.json()
        data = body.get("data") if isinstance(body, dict) else None
        return data if isinstance(data, dict) else {"error": "Unexpected debug_token response", "raw": body}
    except Exception as e:
        return {"error": str(e)}


def summarize_token_for_page_comments(data):
    """
    Print human-readable readiness for posting comments as the Page.
    data: return value of debug_access_token (must be dict with scopes, not None).
    """
    if data is None:
        print("Token debug skipped: set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in .env to inspect scopes.")
        return
    if "error" in data and "is_valid" not in data:
        print(f"debug_token error: {data.get('error')}")
        return
    valid = data.get("is_valid")
    scopes = list(data.get("scopes") or [])
    token_type = data.get("type", "?")
    print(f"Token valid: {valid} | Graph type: {token_type}")
    print(f"Granted scopes ({len(scopes)}): {', '.join(scopes) if scopes else '(none listed)'}")
    # Commenting as the Page on the Page’s own posts typically needs pages_manage_engagement (and posts use pages_manage_posts)
    has_posts = "pages_manage_posts" in scopes
    has_engagement = "pages_manage_engagement" in scopes
    legacy = "publish_pages" in scopes
    ok_comment = has_engagement or legacy
    print(
        "Commenting as Page: "
        + ("LIKELY OK — pages_manage_engagement or publish_pages present" if ok_comment else "MAY FAIL — add pages_manage_engagement to the token")
    )
    print(f"  pages_manage_posts (needed to publish): {'yes' if has_posts else 'NO — add scope'}")
    print(f"  pages_manage_engagement (comments / engagement): {'yes' if has_engagement else 'missing'}")
    if legacy:
        print("  (publish_pages present — legacy scope)")


def post_comment_on_post(post_id, message, page_id=None, page_access_token=None):
    """
    Post a comment as the Page on an existing post (e.g. first comment to boost engagement).
    post_id: the id returned from post_to_facebook_page (photo/video/post id).
    Returns True if comment was posted, False otherwise.
    """
    _, token = _page_creds(page_id, page_access_token)
    if not post_id or not token or not str(message).strip():
        return False
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{post_id}/comments"
    data = {"access_token": token, "message": message[:8000]}
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.ok and response.json().get("id"):
            print(f"First comment posted on {post_id}")
            return True
        if not response.ok:
            print(f"First comment failed: {response.status_code} {response.text[:200]}")
        return False
    except Exception as e:
        print(f"First comment error: {e}")
        return False


def get_recent_posts(limit=50, page_id=None, page_access_token=None):
    """
    Fetch the last N posts published by the Page (message, created_time, id, permalink).
    Use page_id and page_access_token for multi-agent; omit to use config.
    Returns list of dicts with id, message, created_time, permalink_url (or empty list on error).
    """
    pid, token = _page_creds(page_id, page_access_token)
    if not token or not str(token).strip() or not pid or not str(pid).strip():
        return []
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{pid}/posts"
    params = {
        "access_token": token,
        "fields": "id,message,created_time,permalink_url",
        "limit": min(100, max(1, int(limit))),
    }
    try:
        result = None
        for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
            response = requests.get(url, params=params)
            if not _is_rate_limit_response(response):
                response.raise_for_status()
                result = response.json()
                break
            if attempt < RATE_LIMIT_MAX_RETRIES:
                time.sleep(RATE_LIMIT_RETRY_DELAYS[attempt])
        if result is None:
            response.raise_for_status()
            result = response.json()
        data = result.get("data") if isinstance(result, dict) else []
        return list(data) if data else []
    except Exception as e:
        print(f"WARNING: Could not fetch recent Facebook posts for duplicate check: {e}")
        return []
