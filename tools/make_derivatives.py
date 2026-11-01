"""Generate committed web display derivatives for gallery images.

Originals are NEVER modified: Qwen PNGs stay byte-identical in gallery/qwen/
(CI re-verifies their sha256). This script only ADDS web-optimized copies:

    web/public/gallery/qwen/<case_id>.webp   (long edge <= 1000, q82)

The site uses derivatives for thumbnails/inline views and links the original
PNG for full resolution. Deterministic, no network.

    uv run --no-project --with pillow python -I tools/make_derivatives.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "gallery" / "qwen"
DST = REPO / "web" / "public" / "gallery" / "qwen"
LONG_EDGE = 1000
QUALITY = 82


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    made = 0
    for png in sorted(SRC.glob("*.png")):
        webp = DST / (png.stem + ".webp")
        im = Image.open(png)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail((LONG_EDGE, LONG_EDGE), Image.LANCZOS)
        im.save(webp, "WEBP", quality=QUALITY, method=6)
        made += 1
        print(f"derivative: {webp.name} {im.size[0]}x{im.size[1]} {webp.stat().st_size // 1024} KB")
    print(f"[{made}] web derivatives -> {DST.relative_to(REPO)}")


if __name__ == "__main__":
    main()
