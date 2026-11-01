# P7 — Independent Acceptance Review & Delivery Report

**Project:** open-image-showdown (GPT Image 2 vs Qwen-Image 2.1 — Community BYOK Edition)
**Review date:** 2026-11-01 · **Reviewer:** independent engineering agent (mission P7)
**Repo:** `AIwork4me/open-image-showdown` (private until owner publishes) · branch `main` @ `faa14fc`

---

## 1. Executive Verdict: **CONDITIONAL GO**

Everything the mission defined as Definition of Done is built, executed for real, and
machine-verified. The two conditions attached to GO are **owner-side publication actions**,
deliberately not taken by the agent per the mission's authorization boundary ("完成版权和来源审计前，
不要未经 Owner 批准将仓库设为公开"):

| # | Condition | Owner action |
|---|---|---|
| 1 | Repo is currently **private** | Review `docs/P0_AUDIT.md` + `LICENSES_AND_SOURCES.md`, then flip to public when satisfied |
| 2 | GitHub Pages not yet enabled | Settings → Pages → Source: **GitHub Actions** (the workflow `deploy-pages.yml` is ready; its only failure was enablement, the site build itself passed in CI) |

No technical condition remains on the agent side.

## 2. The 12 cases — actual generation results

**12/12 real Qwen-Image 2.1 Quality runs succeeded. Zero failures, zero fallbacks, zero substitutions.**

| Case | Canvas | Wall | VRAM peak | Result |
|---|---|---|---|---|
| case-1 城市生命系统图谱 | 720×1280 | 55.5 s | 14.8 GB | ✅ |
| case-13 数学试卷实拍 | 1024×1024 | 56.7 s | 15.3 GB | ✅ |
| case-14 番茄炒蛋食谱信息图 | 720×1280 | 50.4 s | 14.7 GB | ✅ |
| case-344 NOIR Campaign | 1024×1024 | 55.4 s | 14.5 GB | ✅ |
| case-443 塔可拆解信息图 | 832×1248 | 57.3 s | 14.6 GB | ✅ |
| case-510 Bichon 图标 | 1024×1024 | 57.3 s | 16.3 GB | ✅ |
| case-414 晨间写实摄影 | 832×1248 | 53.3 s | 14.6 GB | ✅ |
| case-434 东京胶片人像 | 720×1280 | 52.5 s | 14.6 GB | ✅ |
| case-419 可颂分镜板 | 1280×720 | 52.5 s | 14.6 GB | ✅ |
| case-390 羊毛毡·日本 | 832×1248 | 57.5 s | 14.5 GB | ✅ |
| case-396 龙类百科海报 | 768×1088 | 46.4 s | 15.0 GB | ✅ |
| case-474 极简旅行海报 | 1280×720 | 51.3 s | 14.5 GB | ✅ |

Profile: bf16-40, cfg 1.0, euler/simple, seed 42, empty negative, `--disable-smart-memory`,
SDPA math · engine `qwen-image-rocm@cbd9e74` · ComfyUI `b5a4321` · weights
`Comfy-Org/Qwen-Image-2.1@aacf31a6`. Every case paid a real fresh TE encode (5.9–7.9 s).
9 of 12 canvases are non-square — **the first non-square runs ever recorded on this GPU
stack**, all within the validated ~1 MP envelope, all labeled as probes in their records.
Per-run telemetry (node timings, per-step times, VRAM sampling, GPU identity, image sha256):
`gallery/qwen/*.run.json`. Full doc: [QWEN_12_CASE_RESULTS.md](QWEN_12_CASE_RESULTS.md).

## 3. Gallery & website — verified in a real browser

Static Vite + React + TS site, keyless by construction, hash-routed (shareable case URLs).

| Check (browser, production build) | Result |
|---|---|
| Home: hero, tagline, 12 cards, 3 real Qwen hero images | ✅ all content present |
| Image loading (15 imgs) | ✅ 15/15 resolve, 0 broken (base-path bug found & fixed during review) |
| Case page (case-443): Qwen panel real image, GPT slot shows "COMMUNITY SUBMISSION PENDING", copy-prompt button, run metadata, source & rights block, share URL + social preview link | ✅ |
| Status badges schema-driven (12 × Open Challenge, honestly 0 reviewed) | ✅ |
| Mobile 375×844: 1-column grid, no horizontal overflow, CTA-only nav | ✅ |
| Screenshots | [docs/screenshots/](screenshots/) — home desktop, case desktop, home mobile |

Social cards: 13 deterministic 1200×630 PNGs generated from real outputs
(`web/public/social/`), each explicitly showing Open Challenge status where applicable.

## 4. BYOK tool — implementation & test results

`tools/generate_gpt.py` + `tools/gpt_client.py`, spec verified against the official docs
(2026-11-01) before implementation: endpoint `POST /v1/images/generations`, pinned
`gpt-image-2-2026-04-21`, custom sizes (16-px multiples, ≤3:1, 0.66–8.3 MP — every case
canvas qualifies, so GPT runs are pixel/aspect-matched to Qwen), quality low/medium/high/auto,
`b64_json` PNG responses.

Verified behaviors (33 tests, all green, no network):

- payload contract: snapshot pin, exact size, n=1, key only in Authorization header (never payload)
- cost gate: exact list price for standard buckets, labeled estimate for custom sizes, `YES` required
- retry policy: 429/5xx retried max 2× with backoff; **4xx never retried** (mission's no-unbounded-paid-retry rule)
- secrets: exception redaction even for leaky transports; artifact self-scan deletes any file containing the key; repo-wide secret scan with **zero allowlist** (it caught the first test fixture, which was then made non-key-shaped)
- freeze integrity: refuses to run if `prompt.txt` sha256 drifts from the manifest
- manual-upload path: covered by evidence tiers (API-evidenced / self-reported / not-accepted)

**Claim discipline:** no live OpenAI API call has been made by this project (it owns no key).
Verification ceiling = contract tests + recorded community runs. The repo states this
everywhere it matters.

## 5. Repository state

- Repo: https://github.com/AIwork4me/open-image-showdown (**private**)
- Branch: `main` @ `faa14fc` (5 commits, clean tree)
- No PRs needed (direct initial delivery on main); all work agent-executed
- Engine dependency untouched: `AIwork4me/qwen-image-rocm` still at `cbd9e74`, branch
  `release/trending-ready-v0.1.0` — zero modifications (P0 constraint respected)

## 6. Actual test evidence

| Gate | Where | Result |
|---|---|---|
| Contract tests (33) | local + GitHub Actions | ✅ 33/33 (`uv … pytest tests/ -q`) |
| Gallery integrity validator | local + GitHub Actions | ✅ PASS (schema, sha256×24 recompute, dims, pins, provenance, duplicates, secret scan, site paths, status truth) |
| Site production build | local + GitHub Actions | ✅ typecheck + bundle (12 gallery PNGs in dist asserted by CI) |
| GitHub CI run | run 41310101060, commit `faa14fc` | ✅ success (22 s) |
| Pages deploy | run 41310101110 | ⏸ site build passed; deploy blocked on Pages enablement (owner action, condition #2) |
| Visual sanity of outputs | pixel statistics | 11/12 "rich"; case-13 (B&W exam paper) plausibly low-variance for its content — human owner should eyeball it |

## 7. Copyright & security risks (residual, ranked)

1. **Prompt provenance chain (low, mitigated).** Prompts republished under the library's MIT
   grant with per-case attribution; 9/12 have public post URLs, 3 (cases 1/13/14) only account
   labels. No library images reused. Takedown path documented; cases are independently swappable.
2. **Qwen Research License (low, mitigated).** Weights verified non-commercial (both HF repos,
   license text archived). Project framed as non-commercial research; Qwen images CC BY-NC 4.0;
   attribution notice included; "Qwen" not used as product name. → Upstream finding **F-1** in
   P0_AUDIT: the *engine repo* still describes the 2.1 weights as "Apache-2.0-based" and its
   gallery as CC-BY-4.0 — owner may want to align that repo too (not modified by us).
3. **GPT-side identity (structural, by design).** Model identity of community images is
   evidence-tiered, never visual. A determined bad actor can fabricate API-shaped records; the
   human review gate + usage/request-id checks raise the bar but cannot make it impossible. The
   site labels tiers visibly.
4. **Secrets (very low).** Zero-allowlist secret scan in CI + CLI self-scan + static site with
   no credential surface. Keys exist only in contributors' environments.
5. **Trademark use (very low).** "GPT Image 2", "Qwen" used descriptively; explicit
   non-affiliation disclaimer everywhere.

## 8. Next 5 most important things

1. **Owner: publish.** Review the audit docs, flip the repo public, enable GitHub Pages
   (Settings → Pages → Source: GitHub Actions) — the deploy workflow is waiting and green
   upstream of that switch. (Also merge/decide `qwen-image-rocm` PR #7 which this project
   depends on — currently unmerged on its release branch.)
2. **Seed the first GPT submission.** One community member (the owner knows many AMD/Qwen
   folks; X posts of case-1/case-419 cards will travel) turning one Open Challenge into a
   Reviewed Comparison proves the whole loop end-to-end — the single highest-leverage event
   for the project.
3. **Launch surface.** Post the 12 social cards (each carries an explicit Open Challenge
   banner) with the X/Reddit/HN copy already implied by the README first screen; enable
   GitHub Discussions (linked in issue templates) for prompt suggestions.
4. **Grow cases via the prompt-suggestion template.** A weekly "case drop" (3–5 new frozen
   manifests, same gate) gives repeatable content and keeps contributors coming back;
   `tools/build_cases.py` makes a new case a 5-minute operation.
5. **Blind-rating mode.** The case pages already randomize A/B sides; a small voting feature
   (per-case, per-visitor localStorage, results published as aggregate counts from real
   records only) turns the showdown into the community judgment the tagline promises —
   without ever inventing numbers.

---

### Definition-of-Done scorecard (mission P7)

| Requirement | Status |
|---|---|
| 12 reviewed Prompt/Case manifests | ✅ frozen, validated, deterministic builder |
| 12 real Qwen images, failures honestly reported | ✅ 12/12 (no failures to report) |
| Per-image provenance | ✅ run records + on-site metadata |
| Usable public gallery | ✅ built & browser-verified (publish = owner action) |
| Copy prompt per case | ✅ verified in browser |
| GPT-missing state real & clear | ✅ verified in browser |
| BYOK tool runs, mock/contract tested | ✅ 33 tests |
| No false E2E-API claim | ✅ stated ceiling everywhere |
| Issue/PR submission path | ✅ templates + submission.json schema |
| Auditable protocol + human review gate | ✅ METHODOLOGY.md |
| Security & license audit | ✅ P0_AUDIT + SECURITY + LICENSES_AND_SOURCES |
| GitHub CPU CI PASS | ✅ run 41310101060 |
| Site build PASS | ✅ local + CI |
| Mobile check PASS | ✅ 375px, no overflow |
