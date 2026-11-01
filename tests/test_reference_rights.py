"""Reference-image rights gates — unit + state tests for the gallery-first release.

These complement tools/validate_gallery.py (which re-verifies everything on
every PR). Here we pin the *semantics*: mirroring is permission-gated,
references are never verified GPT, counts derive from the ledger, and the
case-390 variant chain stays intact.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "gallery" / "reference" / "index.json"


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def load_site() -> dict:
    return json.loads((REPO / "web" / "src" / "data" / "cases.json").read_text(encoding="utf-8"))


def load_manifest(case_id: str) -> dict:
    return json.loads((REPO / "cases" / case_id / "manifest.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- ledger truth

def test_ledger_covers_exactly_the_primary_cases():
    ledger = load_ledger()
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    primary = {c["case_id"] for c in index["cases"] if not load_manifest(c["case_id"]).get("variant_of")}
    ledger_ids = {r["case_id"] for r in ledger["references"]}
    assert ledger_ids == primary, f"ledger {sorted(ledger_ids)} != primary {sorted(primary)}"


def test_all_records_carry_the_audit_fingerprint_fields():
    for r in load_ledger()["references"]:
        assert len(r["image_sha256"]) == 64
        assert r["width"] > 0 and r["height"] > 0
        assert r["source_commit_sha"] == load_ledger()["library_pin"]["commit_sha"]
        assert "UNVERIFIED" in r["model_identity"]
        assert r["display_permission"] in {
            "APPROVED", "EXTERNAL_LINK_ONLY", "PENDING_PERMISSION", "BLOCKED"}
        assert r["prompt_match_level"] in {"EXACT", "DERIVED_TEMPLATE_FILL"}
        # pinned-commit link, never mutable main
        assert r["source_commit_sha"][:7] in r["library_case_url"]
        assert "/blob/main/" not in r["library_case_url"]


def test_no_mirrored_image_without_approval():
    """Gate: any jpg under gallery/reference/images must be APPROVED + verified.
    (Today the directory is empty by design — all 12 are PENDING_PERMISSION.)"""
    images_dir = REPO / "gallery" / "reference" / "images"
    recs = {r["case_id"]: r for r in load_ledger()["references"]}
    for img in images_dir.glob("*.jpg"):
        rec = recs.get(img.stem)
        assert rec is not None, f"{img.name} has no ledger record"
        assert rec["display_permission"] == "APPROVED", f"{img.stem} mirrored without APPROVED"
        assert rec["mirror"]["sha256_verified"] is True


def test_mirror_script_refuses_pending_and_evidenceless(tmp_path):
    """tools/mirror_reference.py must refuse: (a) a PENDING record, (b) an
    APPROVED record without permission evidence. Run against a temp ledger so
    the real repo state (all 12 APPROVED) is not perturbed."""
    script = REPO / "tools" / "mirror_reference.py"
    ledger = load_ledger()

    def run_with(mutate):
        tmp_ledger = tmp_path / "index.json"
        tmp_ledger.write_text(json.dumps(mutate(json.loads(json.dumps(ledger))), ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-I", str(script), "--case", "case-443",
             "--ledger", str(tmp_ledger), "--images-dir", str(tmp_path / "imgs"),
             "--source-file", str(REPO / "gallery" / "reference" / "images" / "case-443.jpg")],
            capture_output=True, text=True, timeout=60, cwd=str(REPO),
        )

    def to_pending(recs):
        recs = [dict(r) for r in recs]
        for r in recs:
            if r["case_id"] == "case-443":
                r["display_permission"] = "PENDING_PERMISSION"
                r["mirror"] = {"path": None, "sha256_verified": False}
        return recs

    proc = run_with(lambda l: {**l, "references": to_pending(l["references"])})
    assert proc.returncode == 1 and "REFUSED" in proc.stderr
    assert "PENDING_PERMISSION" in proc.stderr

    def strip_evidence(recs):
        recs = [dict(r) for r in recs]
        for r in recs:
            if r["case_id"] == "case-443":
                r["permission_evidence"] = None
        return recs

    proc = run_with(lambda l: {**l, "references": strip_evidence(l["references"])})
    assert proc.returncode == 1 and "REFUSED" in proc.stderr
    assert "permission_evidence" in proc.stderr
    # nothing was written by refusals
    assert not (tmp_path / "imgs" / "case-443.jpg").exists()


# ----------------------------------------------------------------- count truth

def test_readme_reference_counts_derive_from_ledger():
    approved = sum(1 for r in load_ledger()["references"] if r["display_permission"] == "APPROVED")
    for readme in ("README.md", "README.zh-CN.md"):
        text = (REPO / readme).read_text(encoding="utf-8")
        marker = [ln for ln in text.splitlines() if "gallery-refs:" in ln]
        assert len(marker) == 1, f"{readme}: exactly one gallery-refs marker expected"
        assert f"gallery-refs:{approved}" in marker[0], (
            f"{readme}: marker must equal ledger-approved count ({approved})")


def test_site_totals_match_ledger():
    ledger = load_ledger()
    site = load_site()
    t = site["totals"]
    assert t["references_total"] == len(ledger["references"])
    assert t["references_approved"] == sum(
        1 for r in ledger["references"] if r["display_permission"] == "APPROVED")
    assert t["cases"] == 12  # primary challenges only
    assert t["variants"] == 1  # case-390t


# ------------------------------------------------- never-verified-GPT semantics

def test_reference_blocks_never_claim_verified_gpt():
    for c in load_site()["cases"]:
        ri = c.get("reference_image")
        if not ri:
            continue
        assert "UNVERIFIED" in ri["model_identity"], f"{c['case_id']}: lost UNVERIFIED marker"
        assert not (ri["renderable"] and ri["display_permission"] != "APPROVED")


def test_display_modes_are_evidence_consistent():
    for c in load_site()["cases"]:
        accepted = [s for s in c["submissions"] if s["state"] == "accepted"]
        if c["display_mode"] == "VERIFIED_GPT_COMPARISON":
            assert accepted, f"{c['case_id']}: verified mode without accepted submission"
        elif c["display_mode"] == "REFERENCE_RECREATION":
            assert c["reference_image"]["renderable"] and c["qwen"]
        else:
            assert c["display_mode"] == "QWEN_ONLY"


# ------------------------------------------------------------ case-390 variant

def test_case_390_variant_chain():
    japan = load_manifest("case-390")
    turkey = load_manifest("case-390t")
    # primary frozen Japan case untouched shape
    assert japan["prompt"]["derivation"]["value"] == "Japan"
    assert turkey["variant_of"] == "case-390"
    assert turkey["prompt"]["derivation"]["value"] == "Turkey"
    assert "infer" in turkey["prompt"]["derivation"]["description"].lower()
    # both prompts derive from the same upstream template
    assert japan["prompt"]["derivation"]["upstream_prompt_sha256"] == \
        turkey["prompt"]["derivation"]["upstream_prompt_sha256"]
    assert japan["prompt"]["sha256"] != turkey["prompt"]["sha256"]
    # both have real ok runs
    for cid in ("case-390", "case-390t"):
        run = json.loads((REPO / "gallery" / "qwen" / f"{cid}.run.json").read_text(encoding="utf-8"))
        assert run["status"] == "ok"
        assert run["image"]["dimensions_match_canvas"]


def test_historical_session_records_all_12_primary_runs():
    hist = json.loads((REPO / "gallery" / "qwen" / "index.json").read_text(encoding="utf-8"))
    assert hist["session"] == "p2-quality-12case"
    ok_ids = {r["case_id"] for r in hist["runs"] if r["status"] == "ok"}
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    primary = {c["case_id"] for c in index["cases"] if not load_manifest(c["case_id"]).get("variant_of")}
    assert primary <= ok_ids, f"primary runs missing from historical session: {primary - ok_ids}"
    assert any("case-390t" in s["file"] for s in hist.get("variant_sessions", []))


# ------------------------------------------------------- aspect disclosure math

def test_aspect_disclosure_flags_recomputed():
    """The 5 mismatch cases must be exactly 13, 344, 443, 396, 419 — recomputed."""
    mismatches = set()
    for r in load_ledger()["references"]:
        ratio_ref = r["width"] / r["height"]
        canvas = r["qwen_canvas"]
        ratio_qwen = canvas["width"] / canvas["height"]
        differs = abs(ratio_ref - ratio_qwen) / ratio_qwen >= 0.02
        assert r["aspect_disclosure_required"] == differs, r["case_id"]
        if differs:
            mismatches.add(r["case_id"].replace("case-", ""))
    assert mismatches == {"13", "344", "443", "396", "419"}


# --------------------------------------------------------- social card policy

def test_social_card_reference_policy():
    """ref_state: an image is used ONLY for APPROVED + sha-verified mirrors."""
    sys.path.insert(0, str(REPO / "tools"))
    import make_social_cards as msc  # noqa: E402

    base = {"display_permission": "PENDING_PERMISSION", "mirror": {"path": None, "sha256_verified": False}}
    state = msc.ref_state("case-443", {"case-443": base})
    assert state["use_image"] is False
    assert state["badge"] == "MODEL UNVERIFIED"

    # approved but no verified mirror -> still no image
    state = msc.ref_state("case-443", {"case-443": {**base, "display_permission": "APPROVED"}})
    assert state["use_image"] is False

    # approved + verified + existing file -> image allowed
    fake = Path(REPO / "gallery" / "qwen" / "case-443.png")
    state = msc.ref_state(
        "case-443",
        {"case-443": {"display_permission": "APPROVED",
                      "mirror": {"path": "gallery/qwen/case-443.png", "sha256_verified": True}}})
    assert state["use_image"] is True and state["mirror"] == fake


def test_social_cards_exist_for_all_cases():
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    for c in index["cases"]:
        assert (REPO / "web" / "public" / "social" / f"{c['case_id']}.png").exists(), c["case_id"]
    assert (REPO / "web" / "public" / "social" / "project.png").exists()


def test_web_derivatives_exist_and_originals_untouched():
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    for c in index["cases"]:
        assert (REPO / "web" / "public" / "gallery" / "qwen" / f"{c['case_id']}.webp").exists()
        # originals stay PNG with run-record sha match (validator recomputes; spot here)
        run = json.loads((REPO / "gallery" / "qwen" / f"{c['case_id']}.run.json").read_text(encoding="utf-8"))
        import hashlib
        digest = hashlib.sha256((REPO / "gallery" / "qwen" / f"{c['case_id']}.png").read_bytes()).hexdigest()
        assert digest == run["image"]["sha256"], c["case_id"]
