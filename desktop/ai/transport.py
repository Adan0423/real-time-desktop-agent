from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from desktop.ai.exceptions import AIClientError

Transport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 RTDA/3.0"
)


def post_json(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout_s: float,
) -> Mapping[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        **dict(headers),
    }
    request = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AIClientError(f"AI provider returned HTTP {exc.code}: {safe_error_body(body)}") from exc
    except urllib.error.URLError as exc:
        raise AIClientError(f"AI provider request failed: {exc.reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AIClientError(f"AI provider request timed out after {timeout_s:.0f}s") from exc
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AIClientError("AI provider returned invalid JSON") from exc
    if not isinstance(decoded, Mapping):
        raise AIClientError("AI provider returned a non-object JSON payload")
    return decoded


def safe_error_body(body: str) -> str:
    compact = " ".join(body.split())
    return compact[:300]
