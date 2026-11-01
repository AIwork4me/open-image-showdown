"""Rights-gated reference image mirror.

Mirrors a reference image from the pinned upstream library commit into
gallery/reference/images/ — REFUSES to run unless the rights ledger
(gallery/reference/index.json) shows display_permission == "APPROVED" for the
case. Verifies the downloaded bytes against the audited image_sha256 before
writing anything. Mutates nothing else; updates the ledger's mirror block only
after a byte-perfect copy exists.

Usage:
    uv run --no-project python -I tools/mirror_reference.py --case case-443 [--force]

Exits 0 on success, 1 on any gate failure. Never retries around a sha mismatch
(a mismatch means upstream changed — re-audit required, not a re-download).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "gallery" / "reference" / "index.json"
IMAGES_DIR = REPO / "gallery" / "reference" / "images"


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True, help="case id, e.g. case-443")
    ap.add_argument("--ledger", default=str(LEDGER), help="ledger path (tests point this at a temp copy)")
    ap.add_argument("--images-dir", default=str(IMAGES_DIR), help="mirror destination dir")
    ap.add_argument("--source-file", default=None,
                    help="offline fallback: local copy of the pinned upstream bytes "
                         "(sha256 must still equal the audited image_sha256)")
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    images_dir = Path(args.images_dir)
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    rec = next((r for r in ledger["references"] if r["case_id"] == args.case), None)
    if rec is None:
        fail(f"{args.case}: no record in the rights ledger")

    if rec["display_permission"] != "APPROVED":
        fail(
            f"{args.case}: display_permission is {rec['display_permission']!r}, not APPROVED. "
            "Record the author's approval (permission_evidence + rights_evidence_url) first — "
            "see docs/PERMISSION_REQUEST_KIT.md."
        )
    if not rec.get("permission_evidence"):
        fail(f"{args.case}: APPROVED but permission_evidence is empty — evidence link is mandatory")

    repo = rec["source_repository"]
    sha = rec["source_commit_sha"]
    path = rec["source_file_path"]
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"

    if args.source_file:
        print(f"reading local pinned-byte copy: {args.source_file}")
        data = Path(args.source_file).read_bytes()
    else:
        print(f"downloading pinned bytes: {url}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            data = Path(tmp.name).read_bytes()

    digest = hashlib.sha256(data).hexdigest()
    if digest != rec["image_sha256"]:
        fail(
            f"{args.case}: sha256 mismatch vs audited fingerprint "
            f"({digest[:16]}… != {rec['image_sha256'][:16]}…). Upstream bytes changed — "
            "re-audit the case before mirroring (do NOT relax this check)."
        )

    images_dir.mkdir(parents=True, exist_ok=True)
    dest = images_dir / f"{args.case}.jpg"
    dest.write_bytes(data)
    rec["mirror"] = {"path": f"gallery/reference/images/{args.case}.jpg", "sha256_verified": True}
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"mirrored {dest} ({len(data)} bytes, sha256 verified) — ledger mirror block updated")


if __name__ == "__main__":
    main()
