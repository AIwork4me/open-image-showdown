# Qwen-Image 2.1 — 12-Case Generation Results

**Run session:** `p2-quality-12case` · 2026-11-01 · all 12 cases **OK**
**Profile:** Quality = bf16 weights, 40 steps, cfg 1.0, euler/simple, seed 42, empty negative prompt
**Hardware:** AMD Radeon RX 7900 XTX 24 GB (gfx1100), native Windows 11 (build 26300), ROCm stack torch 2.12.0+rocm7.14.1 / HIP 7.14.60850
**Software pins:** engine `AIwork4me/qwen-image-rocm` @ `cbd9e74eb121c281d97cf25130cd8de6ffa1be04` (profile manifest `p4-qs-quality-1024x1024`) · ComfyUI `0.43.0` @ `b5a432157de6b8884f81104cd02926adf4d597e4` · weights `Comfy-Org/Qwen-Image-2.1` @ `aacf31a6d48e707f352ecba714cee0680da3479b` (sha256-pinned set: `qwen_image_2.1_bf16.safetensors` DiT / `qwen3vl_8b_bf16.safetensors` TE / `qwen_image_2.1_vae_bf16.safetensors` VAE)
**Server flags:** `--disable-smart-memory`, SDPA math mode (load-bearing on this ROCm/Windows stack)

Full per-run records (websocket node timing, per-step times, VRAM sampling, GPU identity from `/system_stats`): `gallery/qwen/<case>.run.json`. Unedited outputs: `gallery/qwen/<case>.png`.

## Results

| Case | Canvas | Wall (s) | VRAM peak (MB) | TE encode (s) | KSampler (s) | VAE decode (s) | PNG | Image sha256 (12) |
|---|---|---|---|---|---|---|---|---|
| case-1 | 720×1280 | 55.5 | 14,789 | 7.92 | 45.37 | 1.15 | 1.85 MB | `302815bcbf90` |
| case-13 | 1024×1024 | 56.7 | 15,320 | 5.96 | 48.59 | 1.08 | 1.42 MB | `f30f22a231e0` |
| case-14 | 720×1280 | 50.4 | 14,732 | 6.33 | 42.75 | 1.00 | 2.00 MB | `09ab26a0784d` |
| case-344 | 1024×1024 | 55.4 | 14,456 | 5.93 | 47.84 | 1.08 | 1.49 MB | `e1fe81b9def9` |
| case-390 | 832×1248 | 57.5 | 14,459 | 6.14 | 49.26 | 1.07 | 2.11 MB | `5c9e0c4eb9ee` |
| case-396 | 768×1088 | 46.4 | 15,010 | 6.13 | 38.59 | 0.94 | 1.88 MB | `6c9d7e15fa97` |
| case-414 | 832×1248 | 53.3 | 14,610 | 6.12 | 45.46 | 1.07 | 1.57 MB | `db9dbcde3c22` |
| case-419 | 1280×720 | 52.5 | 14,606 | 6.06 | 44.82 | 1.00 | 1.57 MB | `ba9768833478` |
| case-434 | 720×1280 | 52.5 | 14,567 | 6.13 | 44.91 | 0.98 | 1.82 MB | `7b82b4bcfaa3` |
| case-443 | 832×1248 | 57.3 | 14,613 | 6.31 | 49.11 | 1.07 | 1.82 MB | `4081af22c2ad` |
| case-474 | 1280×720 | 51.3 | 14,524 | 5.89 | 43.97 | 1.00 | 1.63 MB | `ab78464ba34e` |
| case-510 | 1024×1024 | 57.3 | 16,346 | 6.28 | 48.92 | 1.06 | 1.02 MB | `db9144e8cc82` |

Wall time = prompt submission → history completion, sequential single-prompt queue (no parallel queueing; matches engine benchmark semantics). Every case's prompt text was new to the server, so each row includes a **real bf16 text-encoder pass** (5.9–7.9 s) — nothing was node-cache hits. KSampler progress events: 39 per run (progress fires at step completion).

## Honest-run notes

1. **No substitutions.** All 12 runs are Quality (bf16-40). No case needed a Fast fallback; no Fast image exists in this gallery, and none is labeled Quality.
2. **First-ever non-square runs on this stack.** The engine repo's entire recorded history is square (1024²/2048²). 9 of the 12 canvases here are non-square (720×1280, 832×1248, 768×1088, 1280×720), chosen at ≤ ~1.05 MP — the same pixel budget as the validated 1024² envelope. All 9 succeeded with VRAM peaks 14.4–14.8 GB (comfortably inside 24 GB); these runs are labeled `canvas_note: probe semantics` in each record.
3. **No seed hunting.** Exactly one image per case at the frozen seed 42, decided before any run. No rerolls occurred; no alternative seeds were generated.
4. **Outputs are unedited.** PNGs are byte-for-byte what ComfyUI returned (sha256 recorded at run time; build-time validation re-verifies them). No crop, recolor, upscale, or retouch.
5. **Server/GPU identity.** Each run record embeds the `/system_stats` device list (`cuda:0 AMD Radeon RX 7900 XTX : native`) — the run cannot silently have happened on another GPU.
6. **Prompt integrity.** Each run re-read `cases/<id>/prompt.txt` and verified its sha256 against the frozen manifest before sending; the driver refuses to run on mismatch.
7. **Image dimension assertion.** Each record asserts the PNG IHDR dimensions equal the planned canvas (`dimensions_match_canvas: true` on all 12).

## Reproduction

Boot the engine server with the Quality profile (equivalent to `quickstart.ps1 -Mode Quality -KeepServer`, minus its benchmark):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  C:\path\to\qwen-image-rocm\phase2-comfyui\launch_comfyui.ps1 `
  -Port 8188 -SdpMode math -ComfyArgs "--disable-smart-memory"
```

Then, from this repo:

```bash
uv run --python 3.12 --with requests --with websocket-client --with jsonschema \
  python -I tools/generate_qwen.py --base-url http://127.0.0.1:8188
```

The driver reuses the engine repo's own `bench/comfyui_client.py` primitives (workflow builder, websocket monitor, schema of run records) with zero modification to the engine repo. Same pinned weights + ComfyUI commit + seed reproduce these images deterministically.

## Licensing of these outputs

Generated with Qwen-Image-2.1 weights under the **Qwen Research License** (non-commercial). The images are published here as research/evaluation artifacts under **CC BY-NC 4.0** with full provenance; any commercial use requires a separate commercial license from the Qwen team.
