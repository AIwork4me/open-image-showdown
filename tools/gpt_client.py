"""Keyless-by-construction OpenAI Images API client for gpt-image-2.

Specification source (verified 2026-11-01, developers.openai.com image-generation
guide + gpt-image-2 model page):

- Endpoint: POST https://api.openai.com/v1/images/generations (JSON body)
- Model: gpt-image-2 / snapshot gpt-image-2-2026-04-21
- size: any "WIDTHxHEIGHT" string with both edges multiples of 16, long:short
  ratio <= 3:1, total pixels within [655_360, 8_294_400]; plus named sizes
  (1024x1024, 1536x1024, 1024x1536, 2048x2048, 2048x1152, 3840x2160,
  2160x3840) and "auto" (default)
- quality: low | medium | high | auto  (gpt-image-2 has no xhigh/max)
- n: images per request (default 1); response data[i].b64_json (default png)
- output_format: png (default) | jpeg | webp; output_compression 0-100 (jpeg/webp)
- background: transparent | opaque | auto
- moderation: auto (default) | low
- safety_identifier recommended for end-user apps (user param deprecated)
- errors: 4xx are user errors (never auto-retry); 429/5xx/timeouts are
  transient (bounded retry with backoff only)
- image_generation_user_error / moderation_blocked carry guidance, not retries

Security invariants enforced by this module:
- the API key is accepted as an argument and used ONLY to build the
  Authorization header; it never enters payloads, records, logs, or errors
  (any exception text is scrubbed through `redact`)
- transport is injectable so tests never touch the network (contract tests)
- retries are bounded (default 2) and only for 429/5xx/network errors
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

API_URL = "https://api.openai.com/v1/images/generations"
MODEL_SNAPSHOT = "gpt-image-2-2026-04-21"
MODEL_ALIAS = "gpt-image-2"

SIZE_MIN_PIXELS = 655_360
SIZE_MAX_PIXELS = 8_294_400
SIZE_MAX_EDGE = 3840
SIZE_RATIO_MAX = 3.0

QUALITY_OPTIONS = ("low", "medium", "high", "auto")
OUTPUT_FORMATS = ("png", "jpeg", "webp")

# Official per-image list prices for gpt-image-2 (USD, developers.openai.com
# pricing table, verified 2026-11-01). Used for the pre-flight cost gate; for
# custom sizes the nearest standard bucket is shown as an *estimate*.
PRICE_TABLE_USD = {
    # (size, quality) -> price per image
    ("1024x1024", "low"): 0.006, ("1024x1024", "medium"): 0.053, ("1024x1024", "high"): 0.211,
    ("1024x1536", "low"): 0.005, ("1024x1536", "medium"): 0.041, ("1024x1536", "high"): 0.165,
    ("1536x1024", "low"): 0.005, ("1536x1024", "medium"): 0.041, ("1536x1024", "high"): 0.165,
}
STANDARD_SIZES = ("1024x1024", "1536x1024", "1024x1536")


def redact(text: str, secret: str | None) -> str:
    """Remove any occurrence of `secret` from text (defensive; urllib should
    never echo headers, but the guarantee is enforced here anyway)."""
    if not secret:
        return text
    return text.replace(secret, "***REDACTED***")


class SizeError(ValueError):
    pass


def parse_size(size: str) -> tuple[int, int]:
    try:
        w_s, h_s = size.lower().split("x")
        w, h = int(w_s), int(h_s)
    except ValueError:
        raise SizeError(f"size must look like WIDTHxHEIGHT, got {size!r}")
    return w, h


def validate_size(size: str) -> tuple[int, int]:
    """Validate a gpt-image-2 custom size against the documented constraints."""
    w, h = parse_size(size)
    if w % 16 != 0 or h % 16 != 0:
        raise SizeError(f"both edges must be multiples of 16, got {w}x{h}")
    if max(w, h) > SIZE_MAX_EDGE:
        raise SizeError(f"max edge is {SIZE_MAX_EDGE}px, got {w}x{h}")
    ratio = max(w, h) / min(w, h)
    if ratio > SIZE_RATIO_MAX:
        raise SizeError(f"aspect ratio must be <= 3:1, {w}x{h} is {ratio:.2f}:1")
    px = w * h
    if px < SIZE_MIN_PIXELS or px > SIZE_MAX_PIXELS:
        raise SizeError(
            f"total pixels must be within [{SIZE_MIN_PIXELS:,}, {SIZE_MAX_PIXELS:,}], "
            f"{w}x{h}={px:,}"
        )
    return w, h


def estimate_cost_usd(size: str, quality: str, n: int = 1) -> tuple[float, bool]:
    """(cost, is_exact). Exact for standard buckets; nearest-bucket estimate
    (scaled by pixel ratio, clamped) for custom sizes. Text input tokens add a
    negligible amount (< $0.01 for these prompts) — stated as such by callers."""
    key = (size, quality)
    if key in PRICE_TABLE_USD:
        return PRICE_TABLE_USD[key] * n, True
    w, h = parse_size(size)
    px = w * h
    base_px = 1024 * 1024
    bucket = {"low": 0.006, "medium": 0.053, "high": 0.211}[quality]
    est = bucket * (px / base_px)
    # portrait/landscape 1.5MP buckets are actually CHEAPER than 1MP square in
    # the official table, so a pixel-scaled square estimate is a safe upper bound
    return est * n, False


@dataclass
class GptImageResult:
    image_bytes: list[bytes] = field(default_factory=list)
    revised_prompt: str | None = None
    usage: dict | None = None
    response_model: str | None = None
    request_id: str | None = None
    raw_without_images: dict | None = None  # full JSON minus b64 payloads (records)


class HttpError(Exception):
    def __init__(self, status: int, body: str, headers: dict):
        super().__init__(f"HTTP {status}: {body[:400]}")
        self.status = status
        self.body = body
        self.headers = headers


def default_transport(url: str, payload: dict, api_key: str, timeout_s: int) -> dict:
    """Real network transport (stdlib only). Returns parsed JSON."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            request_id = resp.headers.get("x-request-id")
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise HttpError(e.code, redact(body, api_key), dict(e.headers)) from None
    except urllib.error.URLError as e:
        raise HttpError(0, f"network error: {e.reason}", {}) from None
    data = json.loads(body)
    if request_id:
        data.setdefault("_request_id", request_id)
    return data


TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


def generate_image(
    *,
    prompt: str,
    size: str,
    quality: str = "medium",
    n: int = 1,
    api_key: str,
    model: str = MODEL_SNAPSHOT,
    output_format: str = "png",
    background: str = "auto",
    safety_identifier: str | None = None,
    transport=default_transport,
    max_retries: int = 2,
    backoff_s: float = 2.0,
    timeout_s: int = 300,
) -> GptImageResult:
    """One bounded, confirmed-by-caller API call. Raises on failure."""
    if quality not in QUALITY_OPTIONS:
        raise ValueError(f"quality must be one of {QUALITY_OPTIONS}")
    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"output_format must be one of {OUTPUT_FORMATS}")
    if not 1 <= n <= 4:
        raise ValueError("n must be within [1, 4] (project policy: default 1)")
    if size != "auto":
        validate_size(size)
    if not api_key or not api_key.strip():
        raise ValueError("api_key is empty — set OPENAI_API_KEY in your shell")

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": n,
        "output_format": output_format,
    }
    if background != "auto":
        payload["background"] = background
    if safety_identifier:
        payload["safety_identifier"] = safety_identifier[:128]

    attempts = max_retries + 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        if attempt:
            time.sleep(backoff_s * (4 ** (attempt - 1)))  # 2s, 8s — bounded
        try:
            data = transport(API_URL, payload, api_key, timeout_s)
            break
        except HttpError as e:
            # defense in depth: even a leaky transport cannot smuggle the key
            # out through exception text
            e.body = redact(e.body, api_key)
            e.args = (f"HTTP {e.status}: {e.body[:400]}",)
            last_error = e
            if e.status in TRANSIENT_STATUSES and attempt < attempts - 1:
                continue
            raise
    else:  # pragma: no cover — loop always breaks or raises
        raise last_error  # type: ignore[misc]

    images = data.get("data") or []
    if not images:
        raise RuntimeError("API returned no images" + _tail_of(data))
    result = GptImageResult()
    for item in images:
        b64 = item.get("b64_json")
        if not b64:
            raise RuntimeError("API item missing b64_json (url-based responses are not "
                               "expected for gpt-image-2)" + _tail_of(item))
        result.image_bytes.append(base64.b64decode(b64))
    result.revised_prompt = images[0].get("revised_prompt")
    result.usage = data.get("usage")
    result.response_model = data.get("model")
    result.request_id = data.get("_request_id") or data.get("id")
    slim = {k: v for k, v in data.items() if k != "data"}
    slim["data"] = [{k: v for k, v in item.items() if k != "b64_json"} for item in images]
    result.raw_without_images = slim
    return result


def _tail_of(obj: object) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False)
    except TypeError:
        s = str(obj)
    return f" — response tail: {s[-300:]}"
