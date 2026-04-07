from typing import Optional, Dict
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def build_utm_url(
    base_url: str,
    *,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    utm_term: Optional[str] = None,
    utm_content: Optional[str] = None,
    extra_params: Optional[Dict[str, str]] = None,
) -> str:
    parsed = urlparse(base_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if utm_source:
        query_params["utm_source"] = utm_source
    if utm_medium:
        query_params["utm_medium"] = utm_medium
    if utm_campaign:
        query_params["utm_campaign"] = utm_campaign
    if utm_term:
        query_params["utm_term"] = utm_term
    if utm_content:
        query_params["utm_content"] = utm_content

    if extra_params:
        query_params.update(extra_params)

    new_query = urlencode(query_params, doseq=True)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))



