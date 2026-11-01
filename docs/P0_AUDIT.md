# P0 Audit — Repos, Configs, Capability, Licensing Freeze

**Project:** open-image-showdown (GPT Image 2 vs Qwen-Image 2.1, Community BYOK Edition)
**Audit date:** 2026-11-01
**Auditor:** AI engineering agent (read-only over both upstream repos; no upstream files modified)
**Status:** COMPLETE — findings below are frozen inputs for P1–P7.

---

## 0. Scope and method

Read-only audit of the two upstream repositories this project depends on:

| Role | Repository | Evidence base |
|---|---|---|
| Generation engine | `AIwork4me/qwen-image-rocm` | Local checkout at `C:\Users\Rocm\Desktop\image`, branch `release/trending-ready-v0.1.0`, HEAD `cbd9e74`, tree clean |
| Prompt source | `freestylefly/awesome-gpt-image-2` | GitHub API (repo metadata + `data/cases.json`, 541 cases, 1,338,334 bytes, sha-pinned copy in build scratch) + HuggingFace API for weight licenses |

Nothing in this audit required GPU execution; all capability numbers are quoted from committed benchmark records in the engine repo.

---

## 1. Engine repo — actual Fast / Quality configurations

Single source of truth: `bench/quickstart_config.py` (`MODES`, lines 80–106) + per-mode manifests under `bench/experiments/`.

| Parameter | **Fast** (E8 default, owner-verdict approved) | **Quality** (this project's mainline) |
|---|---|---|
| Manifest | `p4-qs-fast-1024x1024` | `p4-qs-quality-1024x1024` |
| Steps | 8 (turbo) | **40** |
| CFG | 1.0 | 1.0 |
| Sampler / scheduler | euler / simple | euler / simple |
| DiT weights | `qwen_image_2.1_turbo_int8_convrot.safetensors` (7.26 GB) | **`qwen_image_2.1_bf16.safetensors`** (14.23 GB, **bf16**) |
| Text encoder | `qwen3vl_8b_bf16.safetensors` (17.53 GB, bf16) | same (bf16) |
| VAE | `qwen_image_2.1_vae_bf16.safetensors` | same |
| Attention backend | `ck` (`--use-ck-attention`), sdp math | comfyui-default (`--disable-smart-memory`), sdp math |
| Allowed resolutions | 1024², 2048² | **1024² only** (2048² fail-closed: bf16 VAE decode allocates ~20.25 GB → OOM; evidence `docs/issues/evidence/sdpa-7140-2048-vae-oom.log`) |

- **No fp8 weights exist** for Qwen-Image-2.1 (`docs/weights.md:32-34`): DiT ∈ {bf16, int8_convrot, turbo_bf16, turbo_int8_convrot}; TE ∈ {bf16, int8_convrot, w4a8}; VAE bf16 only.
- The "int8-TE production triple" was **formally REJECTED** as Fast default by owner verdict (issue #5, 2026-11-01) on typography grounds; Fast reverted to E8. This project inherits E8 semantics for any Fast fallback runs — and per mission rules, a Fast image may **never** be labeled Quality.
- Weights revision pin (both modes): HuggingFace `Comfy-Org/Qwen-Image-2.1` @ `aacf31a6d48e707f352ecba714cee0680da3479b`, sha256-verified per file against the in-repo pin table (`bench/quickstart_config.py:53-78`).
- ComfyUI pinned at commit `b5a432157de6b8884f81104cd02926adf4d597e4`; drift fails closed.

**Verdict:** the mission's "Quality = BF16, 40 steps, verified config" corresponds exactly to `p4-qs-quality-1024x1024`. ✅ usable as-is.

## 2. RX 7900 XTX 24 GB — verified capability envelope

From committed records (`bench/results/*`, authoritative summary `docs/benchmarks/REAL_WORLD_LATENCY.md`):

| Capability | Status | Evidence |
|---|---|---|
| 1024×1024 Quality (bf16-40) | ✅ validated, n=9 | warm mean 46.4 s/image, peak VRAM ~15.3 GB (nosmart) |
| 1024×1024 Fast | ✅ validated | warm ~9.2 s/image, peak ~17.4–19.3 GB |
| 2048×2048 Fast | ✅ validated (bounded matrix 3×3) | warm 40.2–40.4 s, sampled peak 8.3–12.6 GB |
| 2048×2048 Quality | ❌ fail-closed OOM | bf16 VAE decode ~20.25 GB tensor |
| **Non-square aspect ratios** | ⚠️ never exercised | `build_workflow()` accepts arbitrary W/H but every recorded run is square |
| Long soak (>13 consecutive 2048 gens) | ❌ untested | documented in engine repo |

- Quality full cold start 67.5 s; fresh-prompt TE encode adds 3–7.5 s on first use of new prompt text.
- Environment snapshot: torch 2.12.0+rocm7.14.1, HIP 7.14.60850, gfx1100, Windows build 26300, Python 3.12.16; SDPA flash/mem-efficient broken on this stack → `QIR_SDP=math` is load-bearing (must launch via `phase2-comfyui/launch_comfyui.ps1` / `launch_wrapper.py`).

**Implication for P2:** run Quality at ~1.0 megapixel budgets (validated envelope); treat each non-square canvas as a probe run recorded as such. See §6.

## 3. Quickstart — support for arbitrary external prompts

- `quickstart.ps1 -Prompt` and `bench/run_comfyui.py --only-prompt` accept only the **3 frozen prompt IDs** in `bench/prompts.json` (`p1-zh-scene`, `p2-en-scene`, `p3-poster-text`). No `--prompt-text` flag exists on the ComfyUI path; unknown IDs raise KeyError.
- Seeds are frozen (`[42, 1337, 20261030]` + cache-busting offsets); no seed CLI on the ComfyUI path.
- `--resolution N` is a square-only override validated against the mode's allowlist.
- The only arbitrary-text CLI is `phase1-diffusers/generate.py` (diffusers + CPU offload, ~239–254 s/image) — too slow, not the benchmarked path.
- **Decision for P2:** do NOT modify the engine repo. Drive a thin client in this repo that imports the engine's `bench/comfyui_client.py` primitives (`build_workflow`, `check_server`, `preflight_workflow`, `post_prompt`, `wait_for_result`, `fetch_image`) against a server booted once with `-KeepServer`. This gives arbitrary prompt/seed/W×H with zero upstream changes. (Engine repo `bench/` stays untouched; its benchmark history is read-only by convention.)

## 4. Reference library — the 12 selected cases

All 12 mission-specified cases exist in `data/cases.json` (IDs are stable): `1, 13, 14, 344, 443, 510, 414, 434, 419, 390, 396, 474`.

**Purity check — all 12 are pure text-to-image:** no reference-image input, no img2img, no editing instructions anywhere in the 12 prompts. ✅

Per-case flags discovered during audit (details frozen into case manifests in P1):

| Ref ID | Title (zh) | Flags |
|---|---|---|
| 1 | 城市生命系统图谱 | Prompt specifies **9:16 vertical**; dense bilingual panel typography |
| 13 | 数学试卷照片 | Prompt text contains original spacing typos ("inblack", "asmartphone") — frozen verbatim; square-ish casual photo |
| 14 | 番茄炒蛋食谱信息图 | Chinese, 9:16 vertical, dense CN typography |
| 344 | NOIR 街头服饰 Campaign | Prompt specifies **1:1**; minimal text (brand + headline) |
| 443 | 塔可爆炸拆解信息图 | Vertical; 5 exact EN labels required |
| 510 | Bichon Shop App 图标 | Square; "Only one icon"; almost no text |
| 414 | 室内晨间写实摄影 | Prompt specifies **2:3**; "no watermark, no text overlay" |
| 434 | 东京街头胶片人像 | Embeds Midjourney-style `--ar 9:16` param + artist signature string "BubbleBrain"; long style chain |
| 419 | 可颂烘焙流程 Storyboard | Prompt specifies **16:9 wide**; 8 panels; heavy EN typography |
| 390 | 羊毛毡国家微缩世界 | **Template variable `[INSERT COUNTRY NAME]` — must be resolved before freeze**; vertical frame |
| 396 | 龙类物种复古百科海报 | A4 vertical (~1:1.414); infographic sections EN |
| 474 | 四城极简旅行海报系列 | Wide multi-destination series; destination-name typography |

`--ar 9:16` (#434) and the signature text are part of the frozen prompt (they were part of the original public prompt); Qwen receives them as literal text, exactly as a GPT Image 2 caller would. Template resolution for #390 is recorded as an explicit derivation in the manifest (chosen value: **Japan** — distinctive landmark + street culture, well-suited to the diorama structure).

## 5. Licensing — the load-bearing facts

### 5.1 Qwen-Image-2.1 weights: Qwen RESEARCH LICENSE (non-commercial)

Verified 2026-11-01 from HuggingFace API + LICENSE file (not assumed):

- `Qwen/Qwen-Image-2.1` → `license:other` → **"Qwen RESEARCH LICENSE AGREEMENT", release date 2026-09-20**.
- `Comfy-Org/Qwen-Image-2.1` → `license:other`, same license (this is the repo the engine downloads from, @ `aacf31a6…`).
- Key terms: grant is **"FOR NON-COMMERCIAL PURPOSES ONLY"** where *Non-Commercial = "for research or evaluation purposes only"*; commercial use needs a separate license; redistribution requires passing the agreement + attribution notice ("Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, Copyright (c) 2026 Hangzhou Tongyi Laboratory Technology Co., Ltd."); cannot use "Qwen" as the primary product name; outputs used to train other AI models require "Built with Qwen" attribution.

**Consequences adopted by this project:**
1. The project is framed and labeled **independent, non-commercial research/evaluation**; no commercial offering of anything Qwen-derived.
2. "Qwen" never appears as the project's primary name (it appears descriptively: "Qwen-Image 2.1").
3. **Qwen-side gallery images are published CC BY-NC 4.0** (not CC BY 4.0) to avoid granting rights the upstream license does not permit. Each Qwen image carries provenance + license notice.
4. README/LICENSES_AND_SOURCES.md carry the required attribution chain.

> **FINDING F-1 (upstream, informational for the owner — NOT fixed here):** the engine repo's `docs/LEGAL_AND_ATTRIBUTION.md` (lines 10–17) still describes the Qwen-Image-2.1 weights as "Alibaba's Qwen license (**Apache-2.0–based** model license)" and its `docs/DATA_LICENSE.md` grants **CC-BY-4.0** (commercial-permitting) over gallery images generated with those weights. For Qwen-Image-2.1 this appears outdated (the Apache-2.0 grant was true of earlier Qwen-Image releases; 2.1 shipped under the Research License on 2026-09-20) and arguably over-grants on the gallery. Recommendation to owner: update that doc and consider CC BY-NC 4.0 for Qwen-2.1-derived gallery images. This audit does not modify the engine repo.

### 5.2 Prompt library: MIT — with an attribution chain caveat

- `freestylefly/awesome-gpt-image-2` is **MIT licensed** (repo metadata; LICENSE file). 35.3k stars, actively maintained.
- Caveat: the MIT grant is made by the library maintainer over a compilation whose individual prompts originate from **third-party authors** (X/Twitter posts for 9 of our 12 cases; 小红书 accounts for cases 1/13/14, which carry **no sourceUrl** — only an account handle label).
- **Consequences adopted:**
  1. We republish prompt **text only**, under the library's MIT grant, with per-case attribution to both the library (canonical GitHub URL) and the labeled original author/source.
  2. We do **not** copy, rehost, or hotlink any of the library's **images** (they are third-party GPT Image 2 outputs; reuse rights are not ours to grant). The GPT side of every case starts **empty** as `OPEN_CHALLENGE`.
  3. Cases 1/13/14's weaker provenance (no sourceUrl) is recorded in their manifests; the library's per-case gallery permalink (`githubUrl`) is cited as the chain of custody.
  4. If an original author objects, the affected case's prompt can be swapped for an original prompt without touching the others (per-case manifests are independent).

### 5.3 This project's license stack (three-way separation, per mission)

| Layer | License |
|---|---|
| Code (tools, site, tests, CI) | **MIT** |
| Case prompts (frozen) | MIT via upstream library, attribution preserved; our manifest metadata: CC BY 4.0 |
| Qwen-side images + run records | **CC BY-NC 4.0** (upstream Qwen Research License constraint) |
| GPT-side community images | Owned by contributors; submitted under contribution terms granting the project a non-exclusive display/distribute license (CC BY 4.0 at submit time) |
| Model weights | Never committed, never rehosted; Qwen Research License (Qwen) / OpenAI terms (GPT) |

### 5.4 GPT Image 2 side (BYOK)

- No OpenAI credentials exist in this project; generation happens **on contributors' machines** with their own keys. The project's tooling is keyless-by-construction (env var read at runtime, never persisted).
- Model/snapshot pin: `gpt-image-2-2026-04-21` (to be re-verified against official docs during P4 implementation before any API call is coded; contract tests use recorded/mocked responses only).
- **Claim discipline:** nothing in this repo may claim end-to-end OpenAI API validation unless a real key run happened and was recorded. Mock/contract tests are the verification ceiling until a community member's real run is contributed.

## 6. Verdict and constraints carried into P1/P2

**Overall: GO** for building the community-BYOK comparison project on this foundation, with these binding constraints:

1. **Quality mainline = bf16-40 @ ~1 MP.** All 12 Qwen images at Quality, pixel budget ≤ ~1.05 MP (matches validated 1024² envelope). Non-square canvases recorded as first-ever non-square runs (probe semantics, honest labeling).
2. **No Fast-as-Quality substitution, ever.** If a case OOMs at Quality, the failure is recorded; a Fast rerun (if any) is a separately labeled variant.
3. **Engine repo untouched**; new repo imports its client primitives by path.
4. **GPT side starts empty**; verification tier labels (`OPEN_CHALLENGE` → `COMMUNITY_SUBMITTED` → `REVIEWED_COMPARISON` / `BLOCKED`) are schema-enforced, never inferred from visual similarity.
5. **Qwen outputs CC BY-NC 4.0**; attribution chain visible on-site.
6. **No upstream image reuse**; prompts only, with attribution.

---
*Evidence snapshots referenced by this audit are preserved in the project scratch area (not committed): upstream `cases.json` (1,338,334 bytes) and `qwen-research-license-2026-09-20.txt` (full LICENSE text as fetched 2026-11-01).*
