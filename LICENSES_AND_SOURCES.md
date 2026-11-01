# Licenses and Sources

This project separates five legal layers. Nothing in one layer overrides another.

| Layer | What it covers | License |
|---|---|---|
| **Code** | `tools/`, `web/`, `tests/`, `.github/`, scripts | **MIT** (see [LICENSE](LICENSE)) |
| **Case prompts** | The 12 frozen prompt texts in `cases/*/prompt.txt` | Republished from the MIT-licensed [awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) library, attribution preserved per case (see each manifest's `reference` block) |
| **Qwen-side images & run records** | `gallery/qwen/*` | **CC BY-NC 4.0** — generated with Qwen-Image-2.1 weights governed by the **Qwen Research License** (non-commercial) |
| **Reference images** | `gallery/reference/images/*` (only when present) | **Remain with their original authors.** Mirrored only with recorded author permission (`APPROVED` in [gallery/reference/index.json](gallery/reference/index.json)); attribution + source links per record |
| **GPT-side community images** | `submissions/**` | Owned by their contributors; submitted under the contribution terms (non-exclusive display/distribute license to this project, CC BY 4.0 display) |
| **Model weights** | never committed, never rehosted | Qwen: Qwen Research License (Alibaba / Hangzhou Tongyi Laboratory). OpenAI: OpenAI terms apply to contributors' own API usage |

## Why Qwen-side images are CC BY-NC 4.0

Qwen-Image-2.1 weights ship under the **Qwen RESEARCH LICENSE AGREEMENT**
(release date 2026-09-20), verified from both [`Qwen/Qwen-Image-2.1`](https://huggingface.co/Qwen/Qwen-Image-2.1)
and [`Comfy-Org/Qwen-Image-2.1`](https://huggingface.co/Comfy-Org/Qwen-Image-2.1)
on 2026-11-01. The grant is "FOR NON-COMMERCIAL PURPOSES ONLY" (research or
evaluation). This project is non-commercial research; publishing its Qwen-side
images under a commercial-permitting license would grant rights the upstream
license does not permit, so they are published CC BY-NC 4.0 with full
provenance. Commercial use of those images or of the weights requires a
separate commercial license from the Qwen team
(model-business@notice.qwencloud.com).

Required attribution notice (per the upstream license):

> Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, Copyright (c) 2026
> Hangzhou Tongyi Laboratory Technology Co., Ltd. All Rights Reserved.

"Qwen" is used here descriptively (naming the model being evaluated); it is not
the primary name of this project, and this project is not affiliated with or
endorsed by Alibaba/Qwen.

## Prompt sources

The 12 prompts originate from the [awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2)
library (MIT). Nine trace to public X/Twitter posts by their original authors;
three (cases 1, 13, 14) carry only a 小红书 account label without a post URL —
recorded as weaker provenance in their manifests. If you are an original author
and want a prompt adjusted or removed, open an issue and it will be handled
promptly (cases are independent; one prompt can be swapped without touching
the others).

One recorded derivation: case-390's upstream prompt contains the template
variable `[INSERT COUNTRY NAME]`, resolved to "Japan" before freezing (both
sha256s in its manifest); the exact-prompt variant `case-390t` resolves it to
"Turkey" (parameter inferred from the reference image, not author-confirmed).

## Reference images (rights gate)

The library displays third-party example images under an opt-out disclaimer
and **does not claim ownership of them** — its MIT grant therefore does not
convey rights to those images, and neither does their availability on GitHub.
This project's policy (enforced by CI):

- **No copying, rehosting, or hotlinking without per-image author permission.**
  All upstream facts are pinned to library commit `63e6176f` (2026-10-14) in
  the [rights ledger](gallery/reference/index.json); the library also enforces
  hotlink protection on its image host.
- A reference image is mirrored into `gallery/reference/images/` **only** after
  its author approves (`display_permission: APPROVED` + evidence link), and the
  mirrored bytes must hash to the audited upstream fingerprint
  ([tools/mirror_reference.py](tools/mirror_reference.py) refuses anything else).
- Until approval, case surfaces show a clearly-labeled link-out card
  ("Community Gallery Reference — Model Unverified · permission pending") —
  never a placeholder image, never an unverified model claim.
- Approvals grant **display with attribution in this non-commercial project
  only**; copyright stays with the author; removal on request at any time.
- Request letters and the recipient list: [docs/PERMISSION_REQUEST_KIT.md](docs/PERMISSION_REQUEST_KIT.md).
  Per-case audit evidence (dimensions, sha256, authors, prompt-match levels):
  [docs/REFERENCE_IMAGE_AUDIT.md](docs/REFERENCE_IMAGE_AUDIT.md).

## GPT Image 2 side

- This project holds **no OpenAI credentials**. GPT-side generation happens on
  contributors' machines with their own keys (BYOK).
- Model pin: `gpt-image-2-2026-04-21` (official snapshot).
- Contributor submissions state their evidence tier (API-evidenced vs
  self-reported). Model identity is never inferred from visual similarity.

## Engine and tooling

- Local Qwen generation reuses [AIwork4me/qwen-image-rocm](https://github.com/AIwork4me/qwen-image-rocm)
  (MIT) as an *external, unmodified* dependency — its client module is imported
  by path; nothing of it is vendored here.
- ComfyUI (GPL-3.0) runs locally at a pinned commit; it is not copied into
  this repository.

## Independence

> Independent community research project. Not affiliated with or endorsed by
> OpenAI, Alibaba/Qwen, or AMD.
