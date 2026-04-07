import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    page_id: str
    page_access_token: str
    graph_api_version: str = "v21.0"
    request_timeout_seconds: int = 30
    max_retries: int = 5
    retry_backoff_seconds: int = 2


def load_settings(env_path: Optional[str] = None) -> Settings:
    if env_path is not None:
        load_dotenv(env_path)
    else:
        load_dotenv()

    page_id = os.getenv("PAGE_ID", "").strip()
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN", "").strip()
    graph_api_version = os.getenv("GRAPH_API_VERSION", "v21.0").strip()

    request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    max_retries = int(os.getenv("MAX_RETRIES", "5"))
    retry_backoff_seconds = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))

    if not page_id:
        raise ValueError("PAGE_ID is required (set it in .env)")
    if not page_access_token:
        raise ValueError("PAGE_ACCESS_TOKEN is required (set it in .env)")

    return Settings(
        page_id=page_id,
        page_access_token=page_access_token,
        graph_api_version=graph_api_version,
        request_timeout_seconds=request_timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )



