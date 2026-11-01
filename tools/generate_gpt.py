r"""BYOK GPT Image 2 generator for open-image-showdown.

Bring Your Own Key: generates the GPT side of a frozen case using YOUR
OpenAI API key, on YOUR machine, and produces a contribution bundle you can
attach to a GitHub Issue / PR. This project never sees or stores your key.

    # 1) put your key in the environment (never in a file)
    set OPENAI_API_KEY=sk-...            # Windows cmd   (or $env:OPENAI_API_KEY in PS)

    # 2) preview cost, confirm interactively, generate exactly one image
    uv run --no-project python -I tools/generate_gpt.py --case case-443

    # 3) non-interactive (CI-ish, still shows the same cost block)
    uv run --no-project python -I tools/generate_gpt.py --case case-443 --yes

Outputs (default under contributions/<case>/gpt-run-<UTC>/):
    image.png           the unedited model output
    run.json            sanitized full run record (no key material anywhere)
    SUBMISSION.md       pre-filled GitHub Issue body for the contribution

Guarantees encoded here (see docs/SECURITY.md):
- key only ever read from the OPENAI_API_KEY environment variable
- explicit cost + model + size confirmation before any paid request
- exactly one image by default (--n to change, capped at 4)
- bounded retries (2, exponential backoff) only on 429/5xx/network errors;
  4xx user errors are never retried
- every written artifact passes a self-scan: if the key string appears in any
  output, the tool refuses to write and aborts
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import gpt_client  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def self_scan(path: Path, secret: str) -> None:
    """Refuse to let key material land in any artifact."""
    blob = path.read_bytes()
    if secret.encode("utf-8") in blob:
        path.unlink(missing_ok=True)
        raise SystemExit(f"SECURITY ABORT: key material detected in {path.name}; file removed")


def load_case(case_id: str) -> tuple[dict, str]:
    case_dir = REPO / "cases" / case_id
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.exists():
        available = sorted(p.name for p in (REPO / "cases").iterdir() if p.is_dir())
        raise SystemExit(f"unknown case {case_id!r}; available: {', '.join(available)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prompt = (case_dir / "prompt.txt").read_text(encoding="utf-8")
    digest = sha256_bytes(prompt.encode("utf-8"))
    if digest != manifest["prompt"]["sha256"]:
        raise SystemExit("prompt.txt does not match the frozen manifest — refusing to run")
    return manifest, prompt


def confirmation_block(case: dict, size: str, quality: str, n: int, api_key: str) -> str:
    cost, exact = gpt_client.estimate_cost_usd(size, quality, n)
    canvas = case["canvas"]
    return (
        "\n================= PAID API REQUEST — CONFIRM =================\n"
        f"  Model    : {gpt_client.MODEL_SNAPSHOT} (pinned snapshot)\n"
        f"  Case     : {case['case_id']} — {case['title']['en']}\n"
        f"  Size     : {size}  (case canvas: {canvas['width']}x{canvas['height']})\n"
        f"  Quality  : {quality}\n"
        f"  Images   : {n}\n"
        f"  Est. cost: ${cost:.3f} {'(official list price)' if exact else '(estimate: custom size, scaled from nearest bucket — actual cost is token-based; check your dashboard)'}\n"
        "  Prompt input tokens add a negligible amount (< $0.01).\n"
        "  Your key stays in this process's memory only. Nothing is sent\n"
        "  anywhere except api.openai.com.\n"
        "==============================================================\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="BYOK GPT Image 2 generator (your key, your machine, one image)"
    )
    ap.add_argument("--case", required=True, help="case id, e.g. case-443")
    ap.add_argument("--quality", default="medium", choices=list(gpt_client.QUALITY_OPTIONS))
    ap.add_argument("--size", default=None,
                    help="override size (default: the case's exact Qwen-matched canvas, "
                         "e.g. 720x1280 — gpt-image-2 accepts custom 16-px-multiple sizes)")
    ap.add_argument("--n", type=int, default=1, help="images per request (default 1, max 4)")
    ap.add_argument("--out", default=None, help="output dir (default contributions/<case>/gpt-run-<ts>)")
    ap.add_argument("--yes", action="store_true",
                    help="skip the interactive confirmation (cost block still printed)")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set. Put YOUR key in the environment "
            "(e.g. `$env:OPENAI_API_KEY = 'sk-...'` in PowerShell) and rerun. "
            "Never paste keys into files, issues, or PRs."
        )

    manifest, prompt = load_case(args.case)
    canvas = manifest["canvas"]
    size = args.size or f"{canvas['width']}x{canvas['height']}"
    if args.size:
        gpt_client.validate_size(size)  # raises with the documented rule text

    print(confirmation_block(manifest, size, args.quality, args.n, api_key))
    if not args.yes:
        answer = input("Type YES to send this paid request: ").strip()
        if answer != "YES":
            raise SystemExit("aborted — nothing was sent, nothing was charged")

    started = datetime.now(timezone.utc)
    try:
        result = gpt_client.generate_image(
            prompt=prompt, size=size, quality=args.quality, n=args.n, api_key=api_key,
        )
    except gpt_client.HttpError as e:
        print(f"\nAPI error (HTTP {e.status}). No retry is possible for this error class "
              f"unless it was transient; nothing further was charged.\n{e}", file=sys.stderr)
        if e.status == 401:
            print("401 usually means the key is invalid or lacks access.", file=sys.stderr)
        raise SystemExit(2)
    finished = datetime.now(timezone.utc)

    out_dir = Path(args.out) if args.out else (
        REPO / "contributions" / manifest["case_id"]
        / f"gpt-run-{started.strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    run = {
        "schema_version": 1,
        "case_id": manifest["case_id"],
        "side": "gpt",
        "model": gpt_client.MODEL_SNAPSHOT,
        "model_alias": gpt_client.MODEL_ALIAS,
        "api_endpoint": gpt_client.API_URL,
        "request": {
            "size": size,
            "quality": args.quality,
            "n": args.n,
            "output_format": "png",
            "seed": None,  # GPT Image has no seed parameter — recorded honestly
        },
        "prompt_sha256": manifest["prompt"]["sha256"],
        "prompt_source": "cases/{case}/prompt.txt (frozen)".format(case=manifest["case_id"]),
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "response": {
            "model": result.response_model,
            "request_id": result.request_id,
            "revised_prompt": result.revised_prompt,
            "usage": result.usage,
            "items": result.raw_without_images.get("data") if result.raw_without_images else None,
        },
        "key_handling": (
            "OPENAI_API_KEY read from environment at runtime; never written to disk, "
            "logs, or any artifact (self-scan enforced)"
        ),
        "verification_tier": "API_EVIDENCED" if result.usage else "SELF_REPORTED_API",
    }
    images_meta = []
    for i, blob in enumerate(result.image_bytes):
        name = "image.png" if len(result.image_bytes) == 1 else f"image-{i + 1}.png"
        p = out_dir / name
        p.write_bytes(blob)
        dims = png_dimensions(blob)
        images_meta.append({
            "file": name, "bytes": len(blob), "sha256": sha256_bytes(blob),
            "width": dims[0] if dims else None, "height": dims[1] if dims else None,
            "edited": False,
        })
    run["images"] = images_meta

    run_path = out_dir / "run.json"
    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # contribution bundle: pre-filled issue body
    img_line = "\n".join(f"- attached: `{m['file']}` (sha256 `{m['sha256'][:16]}…`)"
                         for m in images_meta)
    submission = f"""### GPT Image 2 contribution — {manifest['case_id']}

- **Case ID:** {manifest['case_id']} ({manifest['title']['en']} / {manifest['title']['zh']})
- **Model ID:** `{gpt_client.MODEL_SNAPSHOT}`
- **Prompt SHA256:** `{manifest['prompt']['sha256']}`
- **Generation parameters:** size `{size}`, quality `{args.quality}`, n={args.n}, output png
- **Output image(s):**
{img_line}
- **Source information:** generated locally with `tools/generate_gpt.py` (BYOK); run record `run.json` attached below in the PR / pasted in the issue
- **Rights declaration:** I generated this image with my own OpenAI API key and I have the right to submit it; I grant the open-image-showdown project a non-exclusive, worldwide, royalty-free license to display and distribute it with attribution. ☑
- **Run log (sanitized):** see `run.json` (no key material; self-scanned)

> Maintainer review will promote this to `REVIEWED_COMPARISON` per
> `docs/METHODOLOGY.md`. Model identity is never assumed from visual similarity.
"""
    sub_path = out_dir / "SUBMISSION.md"
    sub_path.write_text(submission, encoding="utf-8")

    # security self-scan on every artifact
    for p in [run_path, sub_path, *[out_dir / m["file"] for m in images_meta]]:
        self_scan(p, api_key)

    print(f"\nOK — {len(images_meta)} image(s) written to {out_dir}")
    print("Next: open a contribution Issue (or PR) and attach the image + run.json;")
    print("      SUBMISSION.md is pre-filled for you.")


if __name__ == "__main__":
    main()
