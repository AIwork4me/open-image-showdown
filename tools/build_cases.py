"""Freeze the 12 showdown cases from the upstream prompt library.

Usage:
    uv run --no-project python -I tools/build_cases.py --source <cases.json> [--out cases]

Reads the upstream snapshot (freestylefly/awesome-gpt-image-2 data/cases.json),
extracts the 12 mission-selected cases, applies the frozen SPEC below, and
writes per-case artifacts:

    cases/case-<ref>/manifest.json   frozen case definition (schema v1)
    cases/case-<ref>/prompt.txt      canonical frozen prompt bytes (UTF-8, no trailing newline)
    cases/index.json                 summary index

Determinism: re-running against the same snapshot is byte-identical. Changing
any frozen field after gallery publication requires a NEW case id (prompt
freeze discipline); this script refuses to silently mutate an existing
manifest's frozen fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA_VERSION = 1

LIBRARY = "freestylefly/awesome-gpt-image-2"
LIBRARY_URL = "https://github.com/freestylefly/awesome-gpt-image-2"
LIBRARY_LICENSE = "MIT"
ENGINE_REPO = "AIwork4me/qwen-image-rocm"
WEIGHTS_REPO = "Comfy-Org/Qwen-Image-2.1"
WEIGHTS_REVISION = "aacf31a6d48e707f352ecba714cee0680da3479b"
COMFYUI_COMMIT = "b5a432157de6b8884f81104cd02926adf4d597e4"

# Quality mainline (engine manifest p4-qs-quality-1024x1024, verbatim params).
QWEN_QUALITY = {
    "mode": "quality",
    "steps": 40,
    "cfg": 1.0,
    "sampler": "euler",
    "scheduler": "simple",
    "negative_prompt": "",
    "seed": 42,
    "engine_manifest": "p4-qs-quality-1024x1024",
}

# Frozen case spec. Canvas budgets stay <= ~1.05 MP (the validated 1024^2
# envelope on RX 7900 XTX); non-square canvases are the first-ever non-square
# runs on this stack and are labeled as such in the run records.
SPEC: list[dict] = [
    {
        "ref_id": 1,
        "title_en": "Urban Metabolism Atlas",
        "title_zh": "城市生命系统图谱",
        "language": "en",
        "aspect": "9:16",
        "width": 720,
        "height": 1280,
        "gpt_size": "1024x1536",
        "notes": [
            "Prompt demands 12 numbered bilingual CN/EN panels — extreme typography stress test.",
            "First-ever non-square canvas on this GPU stack; same ~0.92 MP budget as validated 1024^2.",
        ],
    },
    {
        "ref_id": 13,
        "title_en": "Math Exam Paper Photo",
        "title_zh": "数学试卷实拍照片",
        "language": "en",
        "aspect": "1:1",
        "width": 1024,
        "height": 1024,
        "gpt_size": "1024x1024",
        "notes": [
            "Upstream prompt text contains original spacing typos (e.g. 'inblack', 'asmartphone'); frozen verbatim — fixing them would silently edit the source prompt.",
            "Chinese text content inside an English prompt (mixed-language stress).",
        ],
    },
    {
        "ref_id": 14,
        "title_en": "Tomato & Egg Recipe Infographic",
        "title_zh": "番茄炒蛋食谱信息图",
        "language": "zh",
        "aspect": "9:16",
        "width": 720,
        "height": 1280,
        "gpt_size": "1024x1536",
        "notes": [
            "Dense Chinese typography: 5 recipe steps, chef tips, calligraphy title, seal stamp, signature line.",
        ],
    },
    {
        "ref_id": 344,
        "title_en": "NOIR Streetwear Campaign",
        "title_zh": "NOIR 街头服饰 Campaign",
        "language": "en",
        "aspect": "1:1",
        "width": 1024,
        "height": 1024,
        "gpt_size": "1024x1024",
        "notes": [
            "Prompt itself specifies 1:1; minimal text (brand name + short headline).",
        ],
    },
    {
        "ref_id": 443,
        "title_en": "Exploded Taco Infographic",
        "title_zh": "塔可爆炸拆解信息图",
        "language": "en",
        "aspect": "2:3",
        "width": 832,
        "height": 1248,
        "gpt_size": "1024x1536",
        "notes": [
            "Prompt says 'vertical' without a ratio; 2:3 chosen at the full 1.04 MP budget.",
            "Five exact English labels required (Lettuce/Salsa/Cheese/Meat/Shell).",
        ],
    },
    {
        "ref_id": 510,
        "title_en": "Bichon Shop App Icon",
        "title_zh": "Bichon Shop 拟物 App 图标",
        "language": "en",
        "aspect": "1:1",
        "width": 1024,
        "height": 1024,
        "gpt_size": "1024x1024",
        "notes": [
            "Lightest text load of the 12 — clean-app-icon contrast case.",
        ],
    },
    {
        "ref_id": 414,
        "title_en": "Morning Bedroom Photography",
        "title_zh": "室内晨间写实摄影",
        "language": "en",
        "aspect": "2:3",
        "width": 832,
        "height": 1248,
        "gpt_size": "1024x1536",
        "notes": [
            "Prompt specifies 'Aspect ratio 2:3' and forbids watermarks/text.",
        ],
    },
    {
        "ref_id": 434,
        "title_en": "Tokyo Street Film Portrait",
        "title_zh": "东京街头胶片人像",
        "language": "en",
        "aspect": "9:16",
        "width": 720,
        "height": 1280,
        "gpt_size": "1024x1536",
        "notes": [
            "Embeds a Midjourney-style '--ar 9:16' parameter and the artist signature string 'BubbleBrain'; both kept verbatim — every model receives the same literal text.",
            "Longest single-block style chain among the 12.",
        ],
    },
    {
        "ref_id": 419,
        "title_en": "Croissant Baker Storyboard",
        "title_zh": "可颂烘焙流程 Storyboard",
        "language": "en",
        "aspect": "16:9",
        "width": 1280,
        "height": 720,
        "gpt_size": "1536x1024",
        "notes": [
            "Prompt specifies 'Wide 16:9 layout'; 8 storyboard panels + header/footer typography.",
        ],
    },
    {
        "ref_id": 390,
        "title_en": "Felt Diorama: Japan",
        "title_zh": "羊毛毡微缩世界·日本",
        "language": "en",
        "aspect": "2:3",
        "width": 832,
        "height": 1248,
        "gpt_size": "1024x1536",
        "notes": [
            "Upstream prompt carries the template variable '[INSERT COUNTRY NAME]'; resolved to 'Japan' before freeze (strong identity anchor, rich street life suits the diorama structure). Derivation recorded; upstream sha256 preserved.",
        ],
        "derivation": {
            "type": "template-variable-fill",
            "variable": "[INSERT COUNTRY NAME]",
            "value": "Japan",
        },
    },
    {
        "ref_id": 396,
        "title_en": "Vintage Dragon Encyclopedia",
        "title_zh": "龙类物种复古百科海报",
        "language": "en",
        "aspect": "1:1.414 (A4 portrait)",
        "width": 768,
        "height": 1088,
        "gpt_size": "1024x1536",
        "notes": [
            "A4 ratio approximated as 768x1088 (1:1.4167, 0.84 MP) — closest 16-px-multiple canvas within budget.",
            "Ten infographic sections + engraved-sketch marginalia.",
        ],
    },
    {
        "ref_id": 474,
        "title_en": "Minimal Travel Poster Series",
        "title_zh": "四城极简旅行海报系列",
        "language": "en",
        "aspect": "16:9",
        "width": 1280,
        "height": 720,
        "gpt_size": "1536x1024",
        "notes": [
            "Four named destinations in one wide canvas; destination-name typography in elegant type.",
        ],
    },
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(spec: dict, upstream: dict) -> tuple[dict, bytes]:
    ref_id = spec["ref_id"]
    prompt_text = upstream["prompt"]
    derivation = None
    if spec.get("derivation"):
        d = spec["derivation"]
        var, val = d["variable"], d["value"]
        occurrences = prompt_text.count(var)
        if occurrences != 1:
            raise SystemExit(
                f"case-{ref_id}: derivation variable {var!r} found {occurrences}x (expected 1)"
            )
        derivation = {
            "type": d["type"],
            "variable": var,
            "value": val,
            "upstream_prompt_sha256": sha256_bytes(upstream["prompt"].encode("utf-8")),
            "description": (
                f"Upstream template variable replaced with {val!r} exactly once before freeze; "
                "this is the only modification applied to any of the 12 prompts."
            ),
        }
        prompt_text = prompt_text.replace(var, val)

    prompt_bytes = prompt_text.encode("utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "case_id": f"case-{ref_id}",
        "status": "OPEN_CHALLENGE",
        "blocked_reason": None,
        "title": {
            "en": spec["title_en"],
            "zh": spec["title_zh"],
            "library_title_zh": upstream["title"],
        },
        "category": upstream.get("category"),
        "summary": {
            "one_liner": None,  # filled by hand-authored site copy in P3, not a frozen field
        },
        "reference": {
            "library": LIBRARY,
            "library_url": LIBRARY_URL,
            "library_case_id": ref_id,
            "library_case_url": upstream.get("githubUrl"),
            "library_license": LIBRARY_LICENSE,
            "source_label": upstream.get("sourceLabel"),
            "source_url": upstream.get("sourceUrl") or None,
            "source_note": (
                "Prompt republished under the library's MIT grant with attribution. "
                "The library's image for this case is NOT reused in this project."
            ),
        },
        "prompt": {
            "frozen": True,
            "language": spec["language"],
            "file": "prompt.txt",
            "sha256": sha256_bytes(prompt_bytes),
            "bytes": len(prompt_bytes),
            "chars": len(prompt_text),
            "derivation": derivation,
            "freeze_policy": (
                "prompt.txt is the canonical artifact (UTF-8, no trailing newline). "
                "After gallery publication the prompt text is immutable; corrections "
                "require a new case id."
            ),
        },
        "canvas": {
            "aspect_ratio": spec["aspect"],
            "width": spec["width"],
            "height": spec["height"],
            "megapixels": round(spec["width"] * spec["height"] / 1e6, 4),
            "multiple_of": 16,
        },
        "qwen_plan": {
            **QWEN_QUALITY,
            "width": spec["width"],
            "height": spec["height"],
            "weights_repo": WEIGHTS_REPO,
            "weights_revision": WEIGHTS_REVISION,
            "comfyui_commit": COMFYUI_COMMIT,
            "engine_repo": ENGINE_REPO,
            "gpu": "AMD Radeon RX 7900 XTX 24 GB (gfx1100, native Windows ROCm)",
        },
        "gpt_plan": {
            "model": "gpt-image-2-2026-04-21",
            "model_pinned_snapshot": True,
            "size": spec["gpt_size"],
            "size_note": (
                "Intended closest supported size; exact allowed sizes are frozen in P4 "
                "against the official Images API spec before any contributor run."
            ),
            "byok": True,
            "project_has_no_openai_key": True,
        },
        "verification": {
            "gpt_side": "PENDING_COMMUNITY_SUBMISSION",
            "rules": (
                "Model attribution is never inferred from visual similarity. "
                "COMMUNITY_SUBMITTED -> REVIEWED_COMPARISON only after maintainer "
                "review of run evidence per METHODOLOGY.md."
            ),
        },
        "notes": spec["notes"],
    }
    return manifest, prompt_bytes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="path to upstream cases.json snapshot")
    ap.add_argument("--out", default="cases", help="output directory (default: cases/)")
    ap.add_argument("--force", action="store_true", help="allow rewriting existing frozen manifests")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        library = json.load(f)
    cases = {c["id"]: c for c in library["cases"]}

    out_dir = Path(args.out)
    index = []
    for spec in SPEC:
        ref_id = spec["ref_id"]
        upstream = cases.get(ref_id)
        if upstream is None:
            raise SystemExit(f"upstream snapshot missing case id {ref_id}")
        manifest, prompt_bytes = build_manifest(spec, upstream)

        case_dir = out_dir / f"case-{ref_id}"
        case_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = case_dir / "prompt.txt"
        manifest_path = case_dir / "manifest.json"

        if manifest_path.exists() and not args.force:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            frozen_keys = ("prompt", "canvas", "qwen_plan", "reference", "title", "category")
            for key in frozen_keys:
                if existing.get(key) != manifest[key]:
                    raise SystemExit(
                        f"case-{ref_id}: frozen field {key!r} would change; use --force "
                        "ONLY before first publication (then prefer a new case id)"
                    )

        prompt_path.write_bytes(prompt_bytes)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append(
            {
                "case_id": manifest["case_id"],
                "title_en": manifest["title"]["en"],
                "title_zh": manifest["title"]["zh"],
                "category": manifest["category"],
                "aspect": manifest["canvas"]["aspect_ratio"],
                "width": manifest["canvas"]["width"],
                "height": manifest["canvas"]["height"],
                "prompt_sha256": manifest["prompt"]["sha256"],
                "status": manifest["status"],
            }
        )
        print(f"case-{ref_id}: frozen ({manifest['prompt']['chars']} chars, {manifest['canvas']['width']}x{manifest['canvas']['height']})")

    (out_dir / "index.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "cases": index}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(index)} cases frozen -> {out_dir}/ (index.json written)")


if __name__ == "__main__":
    sys.exit(main())
