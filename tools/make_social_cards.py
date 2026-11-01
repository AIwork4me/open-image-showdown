"""Generate 1200x630 social share cards from real gallery images — dual-panel.

Design contract (gallery-first release):
  LEFT  = Community Gallery Reference. If (and only if) the case's rights
          record is APPROVED + mirrored, the real reference image is shown,
          labeled "Community Gallery Reference — Model Unverified". Otherwise
          a clearly-marked STATUS panel (no image) — never a stand-in picture,
          never a hotlink.
  RIGHT = the real Qwen-Image 2.1 output (always present for generated cases).
  Title "GPT Image 2 vs Qwen-Image 2.1" / subtitle "Same Prompt. You Decide."

    uv run --no-project --with pillow python -I tools/make_social_cards.py

Outputs to web/public/social/ (committed) — deterministic, no network.
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "web" / "public" / "social"
LEDGER = REPO / "gallery" / "reference" / "index.json"

W, H = 1200, 630
BG = (10, 10, 18)
FG = (236, 234, 244)
DIM = (168, 164, 189)
REF = (226, 185, 59)
QWEN = (108, 92, 231)
OPENAI = (16, 163, 127)

TITLE = "GPT Image 2 vs Qwen-Image 2.1"
SUBTITLE = "Same Prompt. You Decide."


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for name in (["seguibl.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def crop_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Cover-crop into w x h (thumbnails only; full views never crop)."""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_w = int(img.height * dst_ratio)
        x = (img.width - new_w) // 2
        img = img.crop((x, 0, x + new_w, img.height))
    else:
        new_h = int(img.width / dst_ratio)
        y = (img.height - new_h) // 2
        img = img.crop((0, y, img.width, y + new_h))
    return img.resize((w, h), Image.LANCZOS)


def crop_contain(img: Image.Image, w: int, h: int, bg=BG) -> Image.Image:
    """Fit entire image inside w x h (letterbox) — never loses content."""
    canvas = Image.new("RGB", (w, h), bg)
    scale = min(w / img.width, h / img.height)
    nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas.paste(resized, ((w - nw) // 2, (h - nh) // 2))
    return canvas


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def status_pill(draw: ImageDraw.ImageDraw, text: str, color, x: int, y: int, max_w: int) -> int:
    f = fit_font(draw, text, 24, max_w - 48)
    tw = draw.textlength(text, font=f)
    rounded(draw, (x, y, x + tw + 44, y + 44), 22, (16, 16, 28))
    draw.ellipse((x + 16, y + 16, x + 28, y + 28), fill=color)
    draw.text((x + 34, y + 8), text, font=f, fill=FG)
    return int(tw) + 44


def ref_state(case_id: str, ledger_recs: dict) -> dict:
    """Pure decision logic for the reference side of a card (unit-tested).
    A reference image is used ONLY for an APPROVED, sha-verified mirror."""
    rec = ledger_recs.get(case_id)
    if rec is None:
        return {"use_image": False, "mirror": None,
                "headline": "COMMUNITY REFERENCE", "sub": "recorded, not mirrored",
                "badge": "MODEL UNVERIFIED", "accent": REF}
    approved = rec["display_permission"] == "APPROVED"
    verified = bool(rec.get("mirror", {}).get("sha256_verified"))
    mirror_rel = rec.get("mirror", {}).get("path")
    mirror_abs = (REPO / mirror_rel) if mirror_rel else None
    use_image = approved and verified and mirror_abs is not None and mirror_abs.exists()
    if use_image:
        sub = "displayed with author permission"
    elif rec["display_permission"] == "EXTERNAL_LINK_ONLY":
        sub = "external link only — not mirrored"
    elif rec["display_permission"] == "BLOCKED":
        sub = "blocked by rights holder"
    else:
        sub = "mirror pending author permission"
    return {"use_image": use_image, "mirror": mirror_abs,
            "headline": "COMMUNITY GALLERY REFERENCE", "sub": sub,
            "badge": "MODEL UNVERIFIED", "accent": REF}


def fit_font(draw: ImageDraw.ImageDraw, text: str, size: int, max_w: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Largest font <= size whose rendered text fits max_w pixels."""
    f = font(size, bold)
    while size > 12 and draw.textlength(text, font=f) > max_w:
        size -= 1
        f = font(size, bold)
    return f


def reference_panel(img: Image.Image, draw: ImageDraw.ImageDraw, x0: int, y0: int, w: int, h: int,
                    state: dict, title: str) -> None:
    """Left panel: real reference image (permission-cleared) or an honest
    status panel. The badge 'Model Unverified' is ALWAYS drawn."""
    if state["use_image"] and state["mirror"]:
        art = crop_contain(Image.open(state["mirror"]).convert("RGB"), w, h - 46, bg=(14, 14, 24))
        img.paste(art, (x0, y0 + 46))
    else:
        draw.rectangle((x0, y0 + 46, x0 + w, y0 + h), fill=(14, 14, 24))
        cy = y0 + 46 + (h - 46) // 2
        head_f = fit_font(draw, state["headline"], 30, w - 36)
        draw.text((x0 + w // 2, cy - 66), state["headline"], font=head_f, fill=state["accent"],
                  anchor="mm")
        draw.text((x0 + w // 2, cy - 18), "— no image until author approves —",
                  font=font(22, bold=False), fill=DIM, anchor="mm")
        sub_f = fit_font(draw, state["sub"], 22, w - 36, bold=False)
        draw.text((x0 + w // 2, cy + 26), state["sub"], font=sub_f, fill=DIM,
                  anchor="mm")
        draw.text((x0 + w // 2, cy + 92), "view at awesome-gpt-image-2 (pinned commit)",
                  font=font(20, bold=False), fill=(120, 118, 140), anchor="mm")
    # header bar over the panel
    draw.rectangle((x0, y0, x0 + w, y0 + 46), fill=(20, 19, 32))
    draw.text((x0 + 14, y0 + 12), state["badge"], font=font(20), fill=state["accent"])
    draw.text((x0 + w - 14, y0 + 12), f"{title[:34]}", font=font(18, bold=False), fill=DIM,
              anchor="ra")


def make_case_card(case: dict, ledger_recs: dict) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    state = ref_state(case["case_id"], ledger_recs)
    left_w = 500
    reference_panel(img, draw, 0, 0, left_w, H, state, case["title"]["en"])

    # divider
    draw.rectangle((left_w, 0, left_w + 4, H), fill=QWEN)

    # right: real Qwen output
    qwen_path = REPO / "gallery" / "qwen" / f"{case['case_id']}.png"
    right_w = W - left_w - 4
    qsize = f"{case['canvas']['width']}x{case['canvas']['height']}"
    if qwen_path.exists():
        art = crop_contain(Image.open(qwen_path).convert("RGB"), right_w, H - 92 - 46, bg=(12, 12, 22))
        img.paste(art, (left_w + 4, 46))
    # right header bar (mirrors the left panel's header)
    draw.rectangle((left_w + 4, 0, W, 46), fill=(20, 19, 32))
    draw.text((left_w + 18, 12), "Qwen-Image 2.1 — Local ROCm Run", font=font(20), fill=(169, 156, 255))
    draw.text((W - 14, 13), f"case {case['case_id'].replace('case-', '#')} · {qsize} · seed 42 · bf16-40",
              font=font(17, bold=False), fill=DIM, anchor="ra")
    # bottom bar: title + subtitle (full width of the right panel, no overlap)
    draw.rectangle((left_w + 4, H - 92, W, H), fill=(16, 15, 26))
    draw.text((left_w + 26, H - 76), TITLE, font=font(30), fill=FG)
    draw.text((left_w + 26, H - 40), SUBTITLE, font=font(23, bold=False), fill=DIM)

    out = OUT_DIR / f"{case['case_id']}.png"
    img.save(out, optimize=True)
    return out


def make_project_card(cases: list[dict], ledger_recs: dict) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    left_w = 560
    draw.rectangle((0, 0, left_w, H), fill=(14, 14, 24))
    inner = left_w - 34 * 2
    title_f = fit_font(draw, TITLE, 46, inner)
    draw.text((34, 52), TITLE, font=title_f, fill=FG)
    draw.text((34, 122), SUBTITLE, font=font(28, bold=False), fill=DIM)
    status_pill(draw, "12 COMMUNITY PROMPTS · MODEL UNVERIFIED", REF, 34, 190, inner)
    status_pill(draw, "13 REAL QWEN RUNS · LOCAL ROCm", QWEN, 34, 252, inner)
    status_pill(draw, "GPT SIDE = BRING YOUR OWN KEY", OPENAI, 34, 314, inner)
    body = fit_font(draw, "references mirror only with author permission", 21, inner, bold=False)
    draw.text((34, 402), "references mirror only with author permission;", font=body, fill=DIM)
    draw.text((34, 434), "no fake pairs, no unverified model claims;", font=body, fill=DIM)
    draw.text((34, 466), "every Qwen image ships with its run record.", font=body, fill=DIM)
    foot = fit_font(draw, "open-image-showdown — independent community research", 20, inner, bold=False)
    draw.text((34, H - 44), "open-image-showdown — independent community research",
              font=foot, fill=(120, 118, 140))
    draw.rectangle((left_w, 0, left_w + 4, H), fill=QWEN)

    with_art = [c for c in cases if (REPO / "gallery" / "qwen" / f"{c['case_id']}.png").exists()][:3]
    strip_w = (W - left_w - 4) // 3
    for i, c in enumerate(with_art):
        art = crop_cover(Image.open(REPO / "gallery" / "qwen" / f"{c['case_id']}.png").convert("RGB"),
                         strip_w, H)
        img.paste(art, (left_w + 4 + i * strip_w, 0))
    return_path = OUT_DIR / "project.png"
    img.save(return_path, optimize=True)
    return return_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ledger_recs = {r["case_id"]: r for r in ledger["references"]}
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    cases = [
        {**c,
         "title": json.loads((REPO / "cases" / c["case_id"] / "manifest.json").read_text(encoding="utf-8"))["title"],
         "status": "OPEN_CHALLENGE",
         "canvas": c}
        for c in index["cases"]
    ]
    # derive real statuses from gallery + submissions
    for c in cases:
        sub_dir = REPO / "submissions" / c["case_id"]
        if sub_dir.exists():
            states = []
            for rec in sub_dir.rglob("submission.json"):
                states.append(json.loads(rec.read_text(encoding="utf-8")).get("review", {}).get("state", "pending"))
            if "accepted" in states:
                c["status"] = "REVIEWED_COMPARISON"
            elif "pending" in states:
                c["status"] = "COMMUNITY_SUBMITTED"

    for c in cases:
        out = make_case_card(c, ledger_recs)
        print(f"card: {out.name} ({out.stat().st_size // 1024} KB)")
    proj = make_project_card(cases, ledger_recs)
    print(f"card: {proj.name} ({proj.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
