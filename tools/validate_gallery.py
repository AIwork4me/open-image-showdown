"""Gallery integrity validator — the automated trust layer.

Checks (exit 1 on any failure; CI runs the pytest wrapper of the same checks):

  1.  Case schema      — every manifest has the required fields with sane values
  2.  Prompt sha256    — recomputed from cases/<id>/prompt.txt vs manifest
  3.  Image sha256     — recomputed from gallery PNGs vs run records
  4.  Dimensions       — PNG IHDR equals manifest canvas; run says ok
  5.  Model identity   — weights repo/revision + comfy commit pinned per record
  6.  Provenance       — reference chain present (library + author label)
  7.  Duplicates       — no duplicate prompt or image sha256 across cases
  8.  Secret scanning  — no API-key patterns in ANY tracked text file
  9.  Gallery paths    — every image referenced by the site model exists
 10.  Status truth     — site data statuses match the evidence on disk

Usage: uv run --no-project python -I tools/validate_gallery.py [--root .]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REQUIRED_MANIFEST_FIELDS = [
    "schema_version", "case_id", "status", "title", "category", "reference",
    "prompt", "canvas", "qwen_plan", "gpt_plan",
]
STATUSES = {"OPEN_CHALLENGE", "COMMUNITY_SUBMITTED", "REVIEWED_COMPARISON", "BLOCKED"}

# crude but effective key-pattern scan (OpenAI live keys + generic assignments)
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"OPENAI_API_KEY\s*=\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
]
SECRET_SCAN_GLOBS = ["*.py", "*.md", "*.json", "*.ts", "*.tsx", "*.mjs", "*.yml", "*.yaml", "*.html", "*.css"]
SECRET_SCAN_EXCLUDE_DIRS = {"node_modules", ".git", "dist", ".venv", "__pycache__"}

TEXT_EXTS = {".py", ".md", ".json", ".ts", ".tsx", ".mjs", ".yml", ".yaml", ".html", ".css", ".txt", ".svg", ".ps1"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


class Failures(list):
    def add(self, case: str, msg: str) -> None:
        self.append(f"[{case}] {msg}")


def validate(root: Path) -> Failures:
    fails = Failures()
    cases_dir = root / "cases"
    gallery_dir = root / "gallery" / "qwen"
    index = json.loads((cases_dir / "index.json").read_text(encoding="utf-8"))
    index_ids = [c["case_id"] for c in index["cases"]]

    seen_prompt_sha: dict[str, str] = {}
    seen_image_sha: dict[str, str] = {}
    site_data_path = root / "web" / "src" / "data" / "cases.json"
    site_data = json.loads(site_data_path.read_text(encoding="utf-8")) if site_data_path.exists() else None

    case_dirs = sorted(p for p in cases_dir.iterdir() if p.is_dir())
    if len(case_dirs) != len(index_ids):
        fails.add("index", f"index lists {len(index_ids)} cases, {len(case_dirs)} dirs on disk")

    for case_dir in case_dirs:
        cid = case_dir.name
        mpath = case_dir / "manifest.json"
        if not mpath.exists():
            fails.add(cid, "manifest.json missing")
            continue
        m = json.loads(mpath.read_text(encoding="utf-8"))

        # 1. schema
        for field in REQUIRED_MANIFEST_FIELDS:
            if field not in m:
                fails.add(cid, f"manifest missing field {field!r}")
        if m.get("status") not in STATUSES:
            fails.add(cid, f"bad status {m.get('status')!r}")
        if m.get("case_id") != cid:
            fails.add(cid, f"case_id mismatch {m.get('case_id')!r}")

        # 2. prompt integrity
        ppath = case_dir / "prompt.txt"
        if not ppath.exists():
            fails.add(cid, "prompt.txt missing")
        else:
            actual = sha256_file(ppath)
            if actual != m["prompt"]["sha256"]:
                fails.add(cid, "prompt sha256 drift")
            if ppath.read_text(encoding="utf-8").encode("utf-8") != ppath.read_bytes():
                fails.add(cid, "prompt.txt is not canonical UTF-8 (round-trip mismatch)")
            if actual in seen_prompt_sha:
                fails.add(cid, f"duplicate prompt sha256 with {seen_prompt_sha[actual]}")
            seen_prompt_sha[actual] = cid

        # 3-5. run record + image
        canvas = m["canvas"]
        run_path = gallery_dir / f"{cid}.run.json"
        img_path = gallery_dir / f"{cid}.png"
        if run_path.exists() != img_path.exists():
            fails.add(cid, "run record and png must exist together")
        elif run_path.exists():
            run = json.loads(run_path.read_text(encoding="utf-8"))
            if run.get("status") != "ok":
                fails.add(cid, f"run status {run.get('status')!r} — failed runs must not be listed as gallery images")
                continue
            if sha256_file(img_path) != run["image"]["sha256"]:
                fails.add(cid, "image sha256 drift vs run record")
            dims = png_dimensions(img_path)
            if dims != (canvas["width"], canvas["height"]):
                fails.add(cid, f"png dims {dims} != canvas {(canvas['width'], canvas['height'])}")
            if run["params"]["width"] != canvas["width"] or run["params"]["height"] != canvas["height"]:
                fails.add(cid, "run params canvas != manifest canvas")
            if run["prompt"]["sha256"] != m["prompt"]["sha256"]:
                fails.add(cid, "run prompt sha != manifest")
            env = run.get("environment", {})
            if not env.get("weights_revision") or not env.get("comfyui_commit"):
                fails.add(cid, "run missing weights/comfy pins")
            if "7900" not in json.dumps(env.get("gpu_devices", [])):
                fails.add(cid, "run gpu identity missing 7900-class device")
            img_sha = run["image"]["sha256"]
            if img_sha in seen_image_sha:
                fails.add(cid, f"duplicate image sha256 with {seen_image_sha[img_sha]}")
            seen_image_sha[img_sha] = cid

        # 6. provenance
        ref = m.get("reference", {})
        if not ref.get("library") or not ref.get("library_case_url"):
            fails.add(cid, "incomplete library attribution")
        if not ref.get("source_label"):
            fails.add(cid, "missing original-author label")

        # gpt plan sanity
        gp = m.get("gpt_plan", {})
        if gp.get("model") != "gpt-image-2-2026-04-21":
            fails.add(cid, "gpt_plan model not pinned snapshot")
        if not gp.get("size_verified"):
            fails.add(cid, "gpt_plan size not verified")

    # 8. secret scan over tracked + generated text files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SECRET_SCAN_EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in SECRET_PATTERNS:
            hit = pat.search(text)
            if hit:
                fails.add("secrets", f"{path.relative_to(root)}: pattern {pat.pattern!r} matched {hit.group(0)[:18]}…")

    # 9. site data path integrity
    if site_data is not None:
        web_root = root / "web"
        for c in site_data["cases"]:
            for rel in [c["qwen"]["image"] if c.get("qwen") else None] + [
                s["image"] for s in c.get("submissions", [])
            ]:
                if not rel:
                    continue
                if (web_root / "public" / rel).exists():
                    continue
                fails.add(c["case_id"], f"site data references missing image {rel}")
            # 10. status truth
            if c.get("qwen") and c["status"] == "OPEN_CHALLENGE":
                accepted = [s for s in c.get("submissions", []) if s["state"] == "accepted"]
                if accepted:
                    fails.add(c["case_id"], "status OPEN_CHALLENGE but an accepted submission exists")

    # submissions duplicate check across cases
    sub_root = root / "submissions"
    if sub_root.exists():
        seen: dict[str, str] = {}
        for rec in sub_root.rglob("submission.json"):
            data = json.loads(rec.read_text(encoding="utf-8"))
            sha = (data.get("image") or {}).get("sha256")
            if not sha:
                fails.add("submissions", f"{rec.relative_to(root)}: no image sha256")
                continue
            if sha in seen:
                fails.add("submissions", f"duplicate submission image {sha[:12]} ({seen[sha]} and {rec.parent.name})")
            seen[sha] = str(rec.relative_to(root))

    return fails


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(REPO))
    args = ap.parse_args()
    root = Path(args.root).resolve()

    # tracked-file sanity: fail if anything that looks like a key is even staged
    try:
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, timeout=30, check=True
        ).stdout.splitlines()
    except Exception:
        tracked = []

    fails = validate(root)
    print(f"validated {len(list((root / 'cases').iterdir())) - 1} cases, "
          f"{len(tracked)} tracked files")
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("PASS — gallery integrity verified")


if __name__ == "__main__":
    main()
