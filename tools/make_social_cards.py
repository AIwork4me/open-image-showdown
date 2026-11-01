"""Generate 1200x630 social share cards from real gallery images.

One card per case (Qwen image + explicit OPEN CHALLENGE / status label) plus a
project card. No placeholder art: if a case has no Qwen image yet, its card is
generated with a plain status panel instead of a fake image.

    uv run --no-project --with pillow python -I tools/make_social_cards.py

Outputs to web/public/social/ (committed) — deterministic, no network.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "web" / "public" / "social"

W, H = 1200, 630
BG = (10, 10, 18)
FG = (236, 234, 244)
DIM = (168, 164, 189)
OPENAI = (16, 163, 127)
QWEN = (108, 92, 231)
WARN = (226, 185, 59)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for name in (["seguibl.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def crop_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Cover-crop into w x h."""
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


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def status_pill(draw: ImageDraw.ImageDraw, text: str, color, x: int, y: int) -> int:
    f = font(26)
    tw = draw.textlength(text, font=f)
    rounded(draw, (x, y, x + tw + 44, y + 48), 24, (16, 16, 28))
    draw.ellipse((x + 18, y + 18, x + 30, y + 30), fill=color)
    draw.text((x + 38, y + 8), text, font=f, fill=FG)
    return int(tw) + 44


def make_case_card(case: dict, idx: int) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # left: real Qwen output (or honest empty panel)
    qwen_path = REPO / "gallery" / "qwen" / f"{case['case_id']}.png"
    left_w = 460
    if qwen_path.exists():
        art = crop_cover(Image.open(qwen_path).convert("RGB"), left_w, H)
        img.paste(art, (0, 0))
    else:
        draw.rectangle((0, 0, left_w, H), fill=(16, 16, 28))
        draw.text((30, H // 2 - 40), "no Qwen run yet", font=font(30, bold=False), fill=DIM)

    # vertical divider
    draw.rectangle((left_w, 0, left_w + 4, H), fill=QWEN)

    # right: text panel
    x0 = left_w + 40
    draw.text((x0, 54), "GPT Image 2  vs  Qwen-Image 2.1", font=font(34), fill=FG)

    title = case["title"]["en"]
    t1 = font(52)
    # simple two-line wrap
    if draw.textlength(title, font=t1) > W - x0 - 40:
        mid = len(title) // 2
        cut = title.rfind(" ", 0, mid) or mid
        draw.text((x0, 130), title[:cut], font=t1, fill=FG)
        draw.text((x0, 192), title[cut:].strip(), font=t1, fill=FG)
        ty = 268
    else:
        draw.text((x0, 150), title, font=t1, fill=FG)
        ty = 230

    draw.text((x0, ty), case["title"]["zh"], font=font(30, bold=False), fill=DIM)

    status = case["status"]
    color = {"OPEN_CHALLENGE": WARN, "COMMUNITY_SUBMITTED": (109, 179, 255),
             "REVIEWED_COMPARISON": (46, 230, 176), "BLOCKED": (224, 85, 85)}[status]
    label = {"OPEN_CHALLENGE": "OPEN CHALLENGE — GPT side pending",
             "COMMUNITY_SUBMITTED": "COMMUNITY SUBMITTED — in review",
             "REVIEWED_COMPARISON": "REVIEWED COMPARISON",
             "BLOCKED": "BLOCKED"}[status]
    status_pill(draw, label, color, x0, ty + 70)

    draw.text((x0, H - 96), f"case {case['case_id'].replace('case-', '#')} · {case['canvas']['width']}x{case['canvas']['height']} · seed 42 · bf16-40",
              font=font(24, bold=False), fill=DIM)
    draw.text((x0, H - 58), "open-image-showdown · Same Prompt. Two Models. You Decide.",
              font=font(24, bold=False), fill=DIM)

    out = OUT_DIR / f"{case['case_id']}.png"
    img.save(out, optimize=True)
    return out


def make_project_card(cases: list[dict]) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # three real strips
    with_art = [c for c in cases if (REPO / "gallery" / "qwen" / f"{c['case_id']}.png").exists()][:3]
    strip_w = W // 3
    for i, c in enumerate(with_art):
        art = crop_cover(Image.open(REPO / "gallery" / "qwen" / f"{c['case_id']}.png").convert("RGB"),
                         strip_w, 330)
        img.paste(art, (i * strip_w, 0))
    draw.rectangle((0, 330, W, 336), fill=QWEN)
    draw.text((48, 372), "GPT Image 2 vs Qwen-Image 2.1", font=font(56), fill=FG)
    draw.text((48, 448), "Same Prompt. Two Models. You Decide.", font=font(34, bold=False), fill=DIM)
    status_pill(draw, "12 REAL QWEN RUNS · GPT SIDE = BRING YOUR OWN KEY", OPENAI, 48, 510)
    draw.text((48, H - 44), "open-image-showdown — independent community research",
              font=font(24, bold=False), fill=DIM)
    out = OUT_DIR / "project.png"
    img.save(out, optimize=True)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
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

    for i, c in enumerate(cases):
        out = make_case_card(c, i)
        print(f"card: {out.name} ({out.stat().st_size // 1024} KB)")
    proj = make_project_card(cases)
    print(f"card: {proj.name} ({proj.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
