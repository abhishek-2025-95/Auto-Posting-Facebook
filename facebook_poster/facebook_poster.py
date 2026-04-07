import mimetypes
from typing import Optional, Dict, Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception

from .config import Settings


class TransientGraphError(Exception):
    pass


def _is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError, TransientGraphError)):
        return True
    return False


class FacebookPoster:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = f"https://graph.facebook.com/{settings.graph_api_version}"
        self.session = requests.Session()

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params is None:
            params = {}
        params.setdefault("access_token", self.settings.page_access_token)

        @retry(
            reraise=True,
            stop=stop_after_attempt(self.settings.max_retries),
            wait=wait_exponential_jitter(initial=self.settings.retry_backoff_seconds, max=30),
            retry=retry_if_exception(_is_transient_error),
        )
        def do_request():
            response = self.session.request(
                method=method,
                url=url,
                params=None if files else params,  # send params in body for multipart
                data=params if files else None,
                files=files,
                timeout=self.settings.request_timeout_seconds,
            )
            if response.status_code >= 500 or response.status_code == 429:
                raise TransientGraphError(f"Transient error {response.status_code}: {response.text}")
            if not response.ok:
                raise requests.HTTPError(f"HTTP {response.status_code}: {response.text}")
            return response.json()

        return do_request()

    def post_text(self, message: str) -> Dict[str, Any]:
        if not message or not message.strip():
            raise ValueError("message must be non-empty")
        path = f"/{self.settings.page_id}/feed"
        params = {"message": message}
        return self._request("POST", path, params=params)

    def post_link(self, link_url: str, message: Optional[str] = None) -> Dict[str, Any]:
        if not link_url:
            raise ValueError("link_url is required")
        path = f"/{self.settings.page_id}/feed"
        params: Dict[str, Any] = {"link": link_url}
        if message:
            params["message"] = message
        return self._request("POST", path, params=params)

    def post_image_from_path(self, image_path: str, caption: Optional[str] = None, published: bool = True) -> Dict[str, Any]:
        if not image_path:
            raise ValueError("image_path is required")
        # MANDATORY: Apply "AI Generated" label before posting (compliance)
        try:
            from ai_label import add_ai_generated_label
            add_ai_generated_label(image_path)
        except Exception:
            pass
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "image/jpeg"
        with open(image_path, "rb") as f:
            files = {"source": (image_path, f, mime_type)}
            params: Dict[str, Any] = {"published": str(published).lower()}
            if caption:
                params["caption"] = caption
            path = f"/{self.settings.page_id}/photos"
            return self._request("POST", path, params=params, files=files)

    def post_image_from_url(self, image_url: str, caption: Optional[str] = None, published: bool = True) -> Dict[str, Any]:
        if not image_url:
            raise ValueError("image_url is required")
        path = f"/{self.settings.page_id}/photos"
        params: Dict[str, Any] = {
            "url": image_url,
            "published": str(published).lower(),
        }
        if caption:
            params["caption"] = caption
        return self._request("POST", path, params=params)



