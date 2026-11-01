# Gallery-First Release — Repository Audit (P0)

Audit date: 2026-11-01 · Auditor: AI assistant (ZCode), for owner review
Scope: current `main` of [AIwork4me/open-image-showdown](https://github.com/AIwork4me/open-image-showdown) prior to the gallery-first visual-comparison release.

## 1. Publication status (dated correction to historical reports)

| Item | State at audit |
|---|---|
| Repository visibility | **PUBLIC** (verified via GitHub API, 2026-11-01) |
| Historical P7 report's "repo is private" statement | **Superseded** — historical reports are NOT altered; this section is the dated correction. `docs/P7_ACCEPTANCE_REPORT.md` remains a historical snapshot. |
| GitHub Pages | **Not enabled** (`GET /repos/…/pages` → 404). `deploy-pages.yml` is merged and will deploy once the owner enables Pages (Settings → Pages → Source: GitHub Actions). README links to `https://aiwork4me.github.io/open-image-showdown/` will 404 until then. |
| Open PRs | None (this branch's draft PR will be the first) |
| `main` HEAD at audit | `a1c0714` (docs(P7): independent acceptance review) |
| Working tree | clean |

## 2. Ground truth of the current release

- **12 frozen cases** in `cases/case-{1,13,14,344,443,510,414,434,419,390,396,474}/` — manifest + canonical `prompt.txt` (sha256-pinned), statuses all `OPEN_CHALLENGE`.
- **12/12 real Qwen-Image 2.1 outputs** in `gallery/qwen/` (PNG + `.run.json` provenance each): bf16, 40 steps, euler/simple, cfg 1.0, seed 42, weights `Comfy-Org/Qwen-Image-2.1@aacf31a6…`, ComfyUI `b5a43215…`, RX 7900 XTX native-Windows ROCm.
- **Reference-library images: NOT in this repo.** Every manifest carries `reference.source_note`: *"The library's image for this case is NOT reused in this project."* `LICENSES_AND_SOURCES.md` §Prompt sources states the library's images are "never copied, rehosted, or hotlinked". The gallery-first release **changes this policy** — under a new, explicit rights gate (see `REFERENCE_IMAGE_AUDIT.md` §Rights), not silently.
- Web site: Vite + React + TS, data built by `web/scripts/build-data.mjs` from frozen artifacts (deterministic, no network), hash-routed (`/#/case/case-N`), static, keyless. Statuses derive from evidence on disk (submissions dir is empty → all OPEN_CHALLENGE).
- Social cards: 13 deterministic 1200×630 PNGs in `web/public/social/` (12 case cards + project card), built by `tools/make_social_cards.py` **from Qwen outputs only** — single-image design today.
- CI: `ci.yml` (pytest incl. gallery-integrity wrapper, ruff, site-data build check, Vite build) — green on `main`. `deploy-pages.yml` blocked only on Pages being enabled.

## 3. Gap analysis vs the gallery-first goal

| # | Gap | Severity | Where fixed in this release |
|---|---|---|---|
| 1 | First screen has **no side-by-side comparison** — README opens with a social banner, prose, badges, then a 12-row table; first real images appear only after ~60 lines | **Critical (the mission's core complaint)** | README redesign (P4) |
| 2 | No reference-image data model: `Reference` type/manifest has no image dims, rights status, model-identity evidence, or prompt-match level | Critical | P3 schema + `gallery/reference/index.json` |
| 3 | No rights/provenance gate for library images (policy was binary: never reuse) | Critical | P2 rights ledger + CI gates |
| 4 | Website hero shows Qwen-only strip; CaseCards are single-thumb | High | P5 |
| 5 | `CompareSlider` overlays two images with no aspect-ratio guard (today only used when a GPT submission exists, so latent) | High | P5 (slider only for equal-aspect pairs; `object-fit: contain` policy) |
| 6 | Case-390 pairing is unsound for comparison: reference depicts **Istanbul/Turkey**, frozen prompt resolved the template to **Japan** | High (verified visually this audit) | `case-390t` Turkey variant (real run) + match-level labeling |
| 7 | Canvas disclosure: 5 reference images differ in aspect from the Qwen canvas (13, 344, 443, 396, 419) — never stated anywhere | High | P1 audit + UI disclosure |
| 8 | Social cards are single-image | Medium | P6 dual-panel design |
| 9 | Site ships full-size PNGs (~1–2 MB each) | Medium | P6 optimized derivatives (originals untouched) |
| 10 | `library_case_url`s point at mutable `main` of the library | Medium | Pinned commit `63e6176f` recorded in the rights ledger |

## 4. Invariants preserved by this release (non-negotiable)

1. The 12 Qwen PNGs, their `.run.json` records, all `prompt.txt` files and their sha256s — **byte-identical** (CI recomputes and enforces).
2. Case statuses remain evidence-driven: reference images are **not** GPT submissions; displaying a library reference never promotes a case to `REVIEWED_COMPARISON`. Only reviewed community GPT submissions (none exist yet) can.
3. No OpenAI API key usage; BYOK contract unchanged.
4. No claim that a reference image is a verified GPT Image 2 output. Reference images are labeled **Community Gallery Reference — Model Unverified** everywhere.
5. Failed/invented images never enter the gallery (validator re-verifies every record on every PR).

## 5. Upstream library state (pinned)

- Reference library: `freestylefly/awesome-gpt-image-2`, HEAD **`63e6176fa01be51c000108dacd72716d3e46784b`** (2026-10-14) — **predates this repo's freeze (2026-11-01), so no upstream drift since freeze**. This commit is the pinned provenance baseline for all reference metadata recorded in this release.
- The library's images live under `data/images/case<N>.jpg` (display-resolution JPEGs), docs under `docs/gallery-part-{1,2}.md` (case anchors `#case-N`).
- The library added **hotlink protection + CDN cache headers for images** (commit `911f2575`, 2026-10-03) — hotlinking is not just disallowed by our policy, it is technically blocked upstream. Any future display must be a rights-cleared local copy.

## 6. What "gallery-first" ships as, given the rights gate

The library's MIT grant covers its own code/docs; its disclaimer explicitly **does not claim ownership of third-party example images** and defers to original rights holders. No per-image redistribution license exists for any of the 12 references (evidence in `REFERENCE_IMAGE_AUDIT.md`). Therefore this release:

- builds the **complete reference-comparison apparatus** (data model, rights ledger, dual-pane UI, dual-panel social cards, CI gates) so approved references light up side-by-side the moment permission lands;
- displays, today, **Qwen images + clearly-labeled reference link-outs** (`Community Gallery Reference — Model Unverified · permission pending`) — no mirrored reference image ships without an APPROVED rights record;
- ships the **bilingual permission-request kit** (`docs/PERMISSION_REQUEST_KIT.md`) the owner sends to the 12 original authors (9 reachable via X; 3 via 小红书 accounts);
- reports display coverage honestly (`N/12 approved`) in README, site, and social cards — the count derives from the ledger, never hardcoded.
