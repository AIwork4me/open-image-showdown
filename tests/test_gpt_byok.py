"""Contract tests for the BYOK gpt-image-2 tooling — no network, no real key.

These pin the API contract (payload shape, snapshot pin, size rules), the
security invariants (key never in payload/artifacts/errors), and the bounded
retry policy. They are the verification ceiling for P4: passing them does NOT
claim a live OpenAI end-to-end run (that requires a contributor's key).
"""

from __future__ import annotations

import base64
import json
import struct
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import gpt_client  # noqa: E402
import generate_gpt  # noqa: E402

FAKE_KEY = "sk-test-DO-NOT-USE-0000000000000000000000000000"


def tiny_png(width: int = 4, height: int = 4) -> bytes:
    """Minimal valid-ish PNG header (dimensions parseable; content irrelevant)."""
    ihdr = struct.pack(">II5B", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\0\0\0\0"


def fake_response(n: int = 1, with_usage: bool = True) -> dict:
    data = {"data": [{"b64_json": base64.b64encode(tiny_png()).decode()} for _ in range(n)]}
    if with_usage:
        data["usage"] = {"input_tokens": 320, "output_tokens": 1056, "total_tokens": 1376}
    data["model"] = gpt_client.MODEL_SNAPSHOT
    data["id"] = "img_req_fake"
    data["_request_id"] = "req_fake_123"
    return data


# ---------------------------------------------------------------- size rules

@pytest.mark.parametrize("size", [
    "720x1280", "1280x720", "832x1248", "1248x832", "768x1088", "1024x1024",
    "1536x1024", "1024x1536", "2048x2048", "2048x1152", "3840x2160", "2160x3840",
])
def test_valid_sizes(size):
    w, h = gpt_client.validate_size(size)
    assert (f"{w}x{h}") == size


@pytest.mark.parametrize("size,reason", [
    ("721x1280", "not multiple of 16"),
    ("720x1281", "not multiple of 16"),
    ("640x2000", "ratio > 3:1"),
    ("3856x2160", "edge > 3840"),
    ("512x512", "too few pixels"),
    ("bogus", "not a size"),
])
def test_invalid_sizes(size, reason):
    with pytest.raises(gpt_client.SizeError):
        gpt_client.validate_size(size)


def test_every_frozen_case_canvas_is_a_valid_gpt_size():
    """P1/P4 interlock: the exact Qwen canvas of each case is a legal
    gpt-image-2 size, so contributors get pixel- and aspect-matched GPT runs."""
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    for case in index["cases"]:
        gpt_client.validate_size(f"{case['width']}x{case['height']}")


# ---------------------------------------------------------------- cost gate

def test_cost_exact_for_standard_bucket():
    cost, exact = gpt_client.estimate_cost_usd("1024x1024", "high", 1)
    assert exact and cost == pytest.approx(0.211)


def test_cost_estimate_for_custom_size_scales_with_pixels():
    # 0.92MP custom estimate must sit below the official 1MP-square price
    # (fewer pixels) and be explicitly labeled an estimate
    est, exact = gpt_client.estimate_cost_usd("720x1280", "medium", 1)
    square_price, _ = gpt_client.estimate_cost_usd("1024x1024", "medium", 1)
    assert not exact
    assert 0 < est < square_price


# ---------------------------------------------------------------- payload contract

def test_payload_shape_and_key_isolation(monkeypatch):
    captured = {}

    def transport(url, payload, api_key, timeout_s):
        captured.update(url=url, payload=payload, header_key=api_key)
        return fake_response()

    result = gpt_client.generate_image(
        prompt="a poster", size="720x1280", quality="medium", n=1,
        api_key=FAKE_KEY, transport=transport,
    )
    assert captured["url"] == gpt_client.API_URL
    p = captured["payload"]
    assert p["model"] == gpt_client.MODEL_SNAPSHOT  # snapshot pin, not alias
    assert p["size"] == "720x1280" and p["quality"] == "medium" and p["n"] == 1
    assert p["output_format"] == "png"
    assert "background" not in p  # auto omitted (default)
    assert FAKE_KEY not in json.dumps(p)  # key lives in the header only
    assert captured["header_key"] == FAKE_KEY
    assert result.image_bytes and result.image_bytes[0].startswith(b"\x89PNG")
    assert result.usage["output_tokens"] == 1056
    assert result.request_id == "req_fake_123"
    # records keep no image payloads
    assert all("b64_json" not in json.dumps(item) for item in result.raw_without_images["data"])


def test_auto_size_skips_validation(monkeypatch):
    def transport(url, payload, api_key, timeout_s):
        return fake_response()
    gpt_client.generate_image(prompt="p", size="auto", api_key=FAKE_KEY,
                              transport=transport)


# ---------------------------------------------------------------- retry policy

def test_transient_429_retried_bounded_then_success(monkeypatch):
    calls = {"n": 0}

    def transport(url, payload, api_key, timeout_s):
        calls["n"] += 1
        if calls["n"] == 1:
            raise gpt_client.HttpError(429, "rate limited", {})
        return fake_response()

    monkeypatch.setattr(gpt_client.time, "sleep", lambda s: None)
    result = gpt_client.generate_image(prompt="p", size="1024x1024",
                                       api_key=FAKE_KEY, transport=transport)
    assert calls["n"] == 2 and result.image_bytes


def test_transient_5xx_retries_capped_never_unbounded(monkeypatch):
    calls = {"n": 0}

    def transport(url, payload, api_key, timeout_s):
        calls["n"] += 1
        raise gpt_client.HttpError(503, "unavailable", {})

    monkeypatch.setattr(gpt_client.time, "sleep", lambda s: None)
    with pytest.raises(gpt_client.HttpError):
        gpt_client.generate_image(prompt="p", size="1024x1024",
                                  api_key=FAKE_KEY, transport=transport, max_retries=2)
    assert calls["n"] == 3  # 1 + 2 retries — hard cap, mission requirement


def test_user_error_4xx_never_retried(monkeypatch):
    calls = {"n": 0}

    def transport(url, payload, api_key, timeout_s):
        calls["n"] += 1
        raise gpt_client.HttpError(400, '{"error": {"code": "moderation_blocked"}}', {})

    with pytest.raises(gpt_client.HttpError):
        gpt_client.generate_image(prompt="p", size="1024x1024",
                                  api_key=FAKE_KEY, transport=transport)
    assert calls["n"] == 1


# ---------------------------------------------------------------- secrets

def test_error_body_redacts_key(monkeypatch):
    # even if a transport leaks the key into an HttpError body, generate_image
    # scrubs it before the exception escapes
    monkeypatch.setattr(gpt_client.time, "sleep", lambda s: None)

    def leaky_transport(url, payload, api_key, timeout_s):
        raise gpt_client.HttpError(500, f"boom {api_key} leak", {})

    with pytest.raises(gpt_client.HttpError) as excinfo:
        gpt_client.generate_image(prompt="p", size="1024x1024",
                                  api_key=FAKE_KEY, transport=leaky_transport)
    assert FAKE_KEY not in str(excinfo.value)
    assert "***REDACTED***" in str(excinfo.value)


def test_self_scan_deletes_file_with_key(tmp_path):
    p = tmp_path / "run.json"
    p.write_text(f'{{"note": "leaked {FAKE_KEY}"}}', encoding="utf-8")
    with pytest.raises(SystemExit, match="SECURITY ABORT"):
        generate_gpt.self_scan(p, FAKE_KEY)
    assert not p.exists()


def test_self_scan_passes_clean_file(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text('{"clean": true}', encoding="utf-8")
    generate_gpt.self_scan(p, FAKE_KEY)  # no raise, file survives
    assert p.exists()


# ---------------------------------------------------------------- CLI gates

def test_cli_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["generate_gpt.py", "--case", "case-443"])
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        generate_gpt.main()


def test_cli_unknown_case_lists_available(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.setattr(sys, "argv", ["generate_gpt.py", "--case", "case-999"])
    with pytest.raises(SystemExit, match="case-443"):  # available cases listed
        generate_gpt.main()


def test_cli_refuses_drifted_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    # tamper with a copy of the repo cases tree
    case = tmp_path / "cases" / "case-1"
    case.mkdir(parents=True)
    src = REPO / "cases" / "case-1"
    (case / "prompt.txt").write_text("tampered prompt", encoding="utf-8")
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    (case / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(generate_gpt, "REPO", tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_gpt.py", "--case", "case-1"])
    with pytest.raises(SystemExit, match="frozen manifest"):
        generate_gpt.main()
