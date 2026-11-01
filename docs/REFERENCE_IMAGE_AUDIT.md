# Reference Image & Prompt Audit — 12 Cases (P1)

Audit date: 2026-11-01 · Verified against upstream library pinned at commit **`63e6176fa01be51c000108dacd72716d3e46784b`** (HEAD of `freestylefly/awesome-gpt-image-2`, 2026-10-14 — predates this repo's 2026-11-01 freeze, so zero upstream drift between freeze and this audit).

Method: every fact below was **programmatically or visually verified this date** — upstream prompt extracted from `docs/gallery-part-{1,2}.md` (```` ```text ```` block), sha256-recomputed and byte-compared to our frozen `prompt.txt`; reference image fetched from `data/images/case<N>.jpg`, hashed, dimensions read pixel-wise; reference theme verified by looking at the actual image (not the caption). Analysis copies live outside this repo; **no reference image byte is committed** (see rights gate, §3).

## 1. Master table

| Case | Reference image (upstream) | Qwen canvas | Aspect relation | Prompt match | Author / source | Theme match |
|---|---|---|---|---|---|---|
| 1 | 941×1672 JPEG (~9:16) | 720×1280 (9:16) | ✅ same | **EXACT** (byte-identical) | 小红书 `insight_express` (no post URL) | ✅ |
| 13 | 647×1149 JPEG (~9:16 portrait) | 1024×1024 (1:1) | ⚠️ **reference portrait, ours square** | **EXACT** | 小红书 `94156710894` (no post URL) | ✅ but reference is a dense full-page Chinese exam photo — a square canvas must re-typeset it |
| 14 | 941×1672 JPEG (~9:16) | 720×1280 (9:16) | ✅ same | **EXACT** | 小红书 `Roy_Jay` (no post URL) | ✅ |
| 344 | 1376×768 JPEG (16:9 landscape) | 1024×1024 (1:1) | ⚠️ **reference landscape, ours square** | **EXACT** | [@Daniel_adsss](https://x.com/Daniel_adsss/status/2048542581638701446) | ✅ (NOIR streetwear banner) |
| 443 | 1254×1254 JPEG (1:1) | 832×1248 (2:3) | ⚠️ **reference square, ours portrait** | **EXACT** | [@Strength04_X](https://x.com/Strength04_X/status/2056018963084226866) | ✅ (labels ride the right edge of the square — crop-sensitive) |
| 510 | 1254×1254 JPEG (1:1) | 1024×1024 (1:1) | ✅ same | **EXACT** | [@iamaiistudio](https://x.com/iamaiistudio/status/2071923809788285125) · [aiistudio.com prompt page](https://aiistudio.com/prompt/i2h-061/bichon-shop) | ✅ |
| 414 | 1024×1536 JPEG (2:3) | 832×1248 (2:3) | ✅ same | **EXACT** | [@ToroJushiAi](https://x.com/ToroJushiAi/status/2053078195482632421) | ✅ |
| 434 | 941×1672 JPEG (~9:16) | 720×1280 (9:16) | ✅ same | **EXACT** | [@BubbleBrain](https://x.com/BubbleBrain/status/2055491616392052887) | ✅ |
| 419 | 1248×832 JPEG (3:2) | 1280×720 (16:9) | ⚠️ **near but unequal** (1.50 vs 1.78) | **EXACT** | [@TechieBySA](https://x.com/TechieBySA/status/2053523784481554759) | ✅ (8-panel storyboard) |
| 390 | 1024×1536 JPEG (2:3) | 832×1248 (2:3) | ✅ same | **DERIVED — template fill** (`[INSERT COUNTRY NAME]` → `Japan`) | [@volkan_iras](https://x.com/volkan_iras/status/2051403524966141980) ([prompt reply](https://x.com/volkan_iras/status/2051403530590638325)) | ❌ **reference is Istanbul/Turkey** (verified visually: Süleymaniye-style mosque, Galata Tower, "TAKSİM" tram, Turkish flags, "ÇAY SİMİT TATLI" sign) — our Japan fill ≠ the depicted country |
| 396 | 768×1376 JPEG (~9:16) | 768×1088 (A4 ≈1:1.414) | ⚠️ **reference taller** | **EXACT** | [@sha_zdiii](https://x.com/sha_zdiii/status/2052237839119835280) | ✅ (dense parchment bestiary poster) |
| 474 | 1080×608 JPEG (16:9) | 1280×720 (16:9) | ✅ same | **EXACT** | [@Taaruk_](https://x.com/Taaruk_/status/2059188921096085888) | ✅ |

Prompt-match verdict: **11/12 byte-exact** (upstream sha256 == frozen sha256, no whitespace drift), **1/12 derived** (case-390, recorded in its manifest with both sha256s). No other template variables exist in any of the 12 upstream prompts. None of the prompts depend on an input/reference image — all are pure text-to-image.

## 2. Reference image fingerprints (upstream copies, library commit `63e6176f`)

| Case | File | sha256 (first 16) | Bytes | Purpose |
|---|---|---|---|---|
| 1 | `data/images/case1.jpg` | `eed45ad06a5db696` | 634,035 | identity pin for any future rights-cleared mirror |
| 13 | `data/images/case13.jpg` | `b37abba16f256a98` | 218,546 | 〃 |
| 14 | `data/images/case14.jpg` | `46ff3923a99f405a` | 492,200 | 〃 |
| 344 | `data/images/case344.jpg` | `035022a432aabbc4` | 75,459 | 〃 |
| 443 | `data/images/case443.jpg` | `ac5352395e25f0dc` | 228,923 | 〃 |
| 510 | `data/images/case510.jpg` | `f2422d47e1ecc53c` | 50,508 | 〃 |
| 414 | `data/images/case414.jpg` | `dd72d7f330c90669` | 171,288 | 〃 |
| 434 | `data/images/case434.jpg` | `dd391dffeec73e83` | 292,402 | 〃 |
| 419 | `data/images/case419.jpg` | `b5b83e4423af8550` | 234,689 | 〃 |
| 390 | `data/images/case390.jpg` | `a1723c725b4cdfc8` | 370,616 | 〃 |
| 396 | `data/images/case396.jpg` | `1eb4b190c8379f6e` | 355,202 | 〃 |
| 474 | `data/images/case474.jpg` | `6e78abf6c2c98907` | 82,415 | 〃 |

Full sha256 values live in `gallery/reference/index.json` (the rights ledger). These fingerprints pin the exact upstream bytes: when a rights approval arrives, the mirrored file must hash to this value (proving we mirrored the audited image, not a different one).

Note on resolution: the library's copies are **display-resolution JPEGs** (e.g. 941×1672, 1254×1254), not original outputs. Any "full resolution" claim about references is therefore about these copies, and is labeled as such.

## 3. Rights gate (the controlling constraint)

- The library's LICENSE is MIT for its own content. Its disclaimer states it "only organizes publicly accessible community prompts and example images", "does not claim ownership of any third-party original content", and requires original-rights-holder authorization for commercial use.
- **No per-image license exists for any of the 12 references.** X posts and 小红书 posts do not carry open licenses; the 3 小红书 cases do not even have a post URL (account label only).
- The library enforces **hotlink protection** on its images (upstream commit `911f2575`) — hotlinking is both disallowed here and blocked there.
- Therefore all 12 start at **`PENDING_PERMISSION`** — display is external-link-only until the rights holder approves. Per-image records, evidence links and the ready-to-send bilingual request kit: `gallery/reference/index.json` + `docs/PERMISSION_REQUEST_KIT.md`. **No reference image may be committed to this repo until its ledger entry is `APPROVED`** (CI-enforced).
- Case-510's second source (`aiistudio.com/prompt/i2h-061/bichon-shop`) suggests the author operates a prompt site; the request letter to that author cites both links.

## 4. Model-identity status of the references

The library presents the images as GPT Image community outputs, but **none carries API-level evidence** of the generating model (no run records, no model/snapshot id). Per this project's methodology, every reference is labeled:

> **Community Gallery Reference — Model Unverified**

References are never called "Verified GPT Image 2" anywhere (README, site, social cards, data model — CI gate #9). A true `VERIFIED_GPT_COMPARISON` still requires a reviewed community submission with run evidence.

## 5. Display-mode decisions per case

| Case | display mode when rights are APPROVED | treatment while PENDING |
|---|---|---|
| 1, 14, 434, 414, 474, 510 | side-by-side (aspects equal) + slider optional | Qwen image + labeled reference link-out |
| 13, 344, 443, 396 | side-by-side **with per-side size disclosure** (aspect mismatch), `contain`, no cropping, no slider | same disclosure, link-out |
| 419 | side-by-side with size disclosure (3:2 vs 16:9) | 〃 |
| 390 | **two pairings**: (a) original reference vs `case-390t` Turkey recreation (exact-prompt, country inferred — see §6), (b) reference vs frozen `case-390` Japan run shown as *derived-prompt theme variant*, explicitly not an exact match | Japan run + link-out; `case-390t` shows beside it as soon as it exists (own image, no rights issue) |

**Slider policy**: the drag overlay is only used when both sides share an aspect ratio (within 1%); otherwise fixed side-by-side with `object-fit: contain` and letterboxing — never `cover` (would amputate the taco labels, exam-paper margins, or poster panels).

## 6. Case-390 remediation (critical-case fix)

The upstream image depicts **Istanbul, Turkey** while our frozen prompt resolved `[INSERT COUNTRY NAME]` → `Japan`. The frozen Japan case is **kept byte-identical** (prompt, run record, sha256). The fix adds a supplementary variant case:

- `case-390t` — same upstream template resolved to **Turkey**, with the derivation note stating the country was **inferred from the reference image's content (Istanbul landmarks), not confirmed by the author**. Prompt-match level against the reference: `EXACT_TEMPLATE_FILL_INFERRED`.
- A **real Qwen run** was executed for `case-390t` (same engine pins, seed 42, 832×1248) so the exact-prompt pairing is displayable the day reference rights arrive.
- Neither `case-390` (Japan) nor its run record changes. No claim of "exact prompt match" is made for the Japan pairing — it is labeled a theme variant.

## 7. Replacement decisions

**No case replaced.** All 12 pass the selection policy once disclosures are in place: prompts exact (11) or recorded-derivation (1), themes consistent (390 handled via variant), rights pending but uniform (all 12 equal footing — replacing a case would not improve rights posture since every library image shares the same status). Numbers stay 12.
