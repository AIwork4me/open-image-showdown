"""Generate the 12 frozen showdown cases locally with Qwen-Image 2.1 (Quality).

Drives a running ComfyUI server (booted by the engine repo's launcher with
Quality flags) through the engine's own battle-tested client primitives —
``bench/comfyui_client.py`` — with zero modifications to the engine repo.

Server boot (mirror of quickstart.ps1 Mode=Quality, minus its benchmark):

    powershell -NoProfile -ExecutionPolicy Bypass -File ^
      <engine>\phase2-comfyui\launch_comfyui.ps1 -Port 8189 ^
      -SdpMode math -ComfyArgs "--disable-smart-memory"

Then:

    uv run --python 3.12 --with requests --with websocket-client --with jsonschema ^
      python -I tools/generate_qwen.py --base-url http://127.0.0.1:8189

Per case this writes:
    gallery/qwen/<case_id>.png         unedited model output
    gallery/qwen/<case_id>.run.json    full provenance record
and finally gallery/qwen/index.json (session summary).

Honesty rules encoded here:
- prompt bytes are sha256-verified against the frozen manifest before send;
- the output PNG's IHDR dimensions must equal the manifest canvas (or the
  record is marked mismatch);
- a failed/OOM case is recorded as a failure — never skipped silently, never
  retried into a different mode;
- exactly one image per case (seed from the manifest, no seed hunting).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

DEFAULT_ENGINE = Path(r"C:\Users\Rocm\Desktop\image")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse IHDR (bytes 16-24) of a PNG stream."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    import struct

    width, height = struct.unpack(">II", data[16:24])
    return width, height


def git_head(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def comfyui_commit(engine: Path) -> str | None:
    head_file = engine / "phase2-comfyui" / "ComfyUI" / ".git" / "HEAD"
    try:
        ref = head_file.read_text(encoding="utf-8").strip()
        if ref.startswith("ref: "):
            ref_path = engine / "phase2-comfyui" / "ComfyUI" / ".git" / ref[5:]
            return ref_path.read_text(encoding="utf-8").strip()
        return ref
    except Exception:
        return None


def execute(base_url: str, client, wf: dict) -> tuple[float, dict, dict, str | None]:
    """One monitored execution; mirrors engine run_comfyui._execute."""
    mon = client.RunMonitor(base_url)
    mon.start()
    history: dict = {}
    error: str | None = None
    try:
        t0 = time.perf_counter()
        prompt_id = client.post_prompt(base_url, wf, client_id=mon.client_id)
        history = client.wait_for_result(base_url, prompt_id, timeout_s=1800)
        total_s = time.perf_counter() - t0
    except Exception as exc:  # server-side execution errors surface here
        total_s = -1.0
        error = f"{type(exc).__name__}: {exc}"
    finally:
        mon.stop()
    return total_s, mon.summarize(wf), history, error


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", default=str(DEFAULT_ENGINE),
                    help="engine repo root (default: %(default)s)")
    ap.add_argument("--base-url", default="http://127.0.0.1:8189")
    ap.add_argument("--cases", default=None,
                    help="comma-separated case ids (default: all frozen cases)")
    ap.add_argument("--out", default=str(REPO / "gallery" / "qwen"))
    ap.add_argument("--session", default=None, help="session tag (default: UTC timestamp)")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = ap.parse_args()

    engine = Path(args.engine).resolve()
    if not (engine / "bench" / "comfyui_client.py").exists():
        raise SystemExit(f"engine repo not found at {engine}")
    sys.path.insert(0, str(engine))
    from bench import comfyui_client, quickstart_config  # noqa: E402

    quality = quickstart_config.MODES["quality"]
    manifest_name = quality["manifest"]
    from bench.experiments import load_manifest  # noqa: E402
    q_manifest = load_manifest(manifest_name)

    # -- freeze-integrity + environment blocks (shared by all records) ------
    engine_head = git_head(engine)
    comfy_commit = comfyui_commit(engine)
    index = json.loads((REPO / "cases" / "index.json").read_text(encoding="utf-8"))
    case_ids = [c["case_id"] for c in index["cases"]]
    if args.cases:
        wanted = [c.strip() for c in args.cases.split(",") if c.strip()]
        unknown = [c for c in wanted if c not in case_ids]
        if unknown:
            raise SystemExit(f"unknown case ids: {unknown}")
        case_ids = wanted

    base_url = args.base_url.rstrip("/")
    print(f"[engine]   {engine} @ {engine_head}")
    print(f"[comfyui]  {comfy_commit}")
    print(f"[weights]  {quickstart_config.WEIGHTS_REVISION}")
    print(f"[profile]  {manifest_name}: steps={q_manifest['steps']} cfg={q_manifest['cfg']} "
          f"unet={q_manifest['unet']}")
    print(f"[server]   {base_url} — checking…")
    comfyui_client.check_server(base_url)  # refuses unless a 7900-class device is present
    sys_stats = comfyui_client._get(base_url + "/system_stats").json()
    gpu_names = [d.get("name", "?") for d in sys_stats.get("devices", [])]
    print(f"[gpu]      {gpu_names}")

    env_block = {
        "engine_repo": "AIwork4me/qwen-image-rocm",
        "engine_commit": engine_head,
        "comfyui_commit": comfy_commit,
        "weights_repo": "Comfy-Org/Qwen-Image-2.1",
        "weights_revision": quickstart_config.WEIGHTS_REVISION,
        "engine_manifest": manifest_name,
        "gpu_devices": sys_stats.get("devices", []),
        "comfyui_version": sys_stats.get("system", {}).get("comfyui_version"),
        "os": sys.platform,
        "client_python": sys.version.split()[0],
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    session = args.session or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary: list[dict] = []

    for case_id in case_ids:
        case_dir = REPO / "cases" / case_id
        manifest = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))
        prompt_bytes = (case_dir / "prompt.txt").read_bytes()
        prompt_sha = sha256_bytes(prompt_bytes)
        if prompt_sha != manifest["prompt"]["sha256"]:
            raise SystemExit(
                f"{case_id}: prompt.txt sha256 {prompt_sha[:12]}… != frozen "
                f"{manifest['prompt']['sha256'][:12]}… — refusing to run (freeze broken)"
            )
        plan = manifest["qwen_plan"]
        png_path = out_dir / f"{case_id}.png"
        rec_path = out_dir / f"{case_id}.run.json"
        if png_path.exists() and not args.force:
            print(f"{case_id}: SKIP (output exists, --force to redo)")
            continue

        square = plan["width"] == plan["height"]
        record: dict = {
            "schema_version": 1,
            "case_id": case_id,
            "session": session,
            "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "prompt": {
                "sha256": prompt_sha,
                "chars": manifest["prompt"]["chars"],
                "verified_against_manifest": True,
            },
            "params": {
                "mode": plan["mode"],
                "steps": plan["steps"],
                "cfg": plan["cfg"],
                "sampler": plan["sampler"],
                "scheduler": plan["scheduler"],
                "seed": plan["seed"],
                "negative_prompt": plan["negative_prompt"],
                "width": plan["width"],
                "height": plan["height"],
                "unet": q_manifest["unet"],
                "clip": q_manifest["clip"],
                "vae": q_manifest["vae"],
                "weight_dtype": q_manifest["weight_dtype"],
                "tiled_vae": q_manifest["tiled_vae"],
                "server_flags": q_manifest.get("server_flags", []),
            },
            "canvas_note": (
                "first non-square canvas in this GPU stack's recorded history — "
                "probe semantics, same ~<=1.05 MP budget as validated 1024^2"
                if not square else "validated square budget"
            ),
            "environment": env_block,
        }

        print(f"{case_id}: generating {plan['width']}x{plan['height']} "
              f"steps={plan['steps']} seed={plan['seed']} …", flush=True)
        wf = comfyui_client.build_workflow(
            unet=q_manifest["unet"], clip=q_manifest["clip"], vae=q_manifest["vae"],
            prompt=prompt_bytes.decode("utf-8"), negative=plan["negative_prompt"],
            width=plan["width"], height=plan["height"],
            steps=plan["steps"], seed=plan["seed"],
            sampler=plan["sampler"], scheduler=plan["scheduler"],
            cfg=plan["cfg"], weight_dtype=q_manifest["weight_dtype"],
            tiled_vae=q_manifest["tiled_vae"],
        )
        if case_id == case_ids[0]:
            comfyui_client.preflight_workflow(base_url, wf)

        total_s, mon_summary, history, error = execute(base_url, comfyui_client, wf)
        record["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record["timing"] = {"total_s": round(total_s, 3) if total_s > 0 else None}
        record["monitor"] = mon_summary

        if error is None:
            try:
                image_bytes = comfyui_client.fetch_image(base_url, history)
            except Exception as exc:
                error = f"fetch_image failed: {type(exc).__name__}: {exc}"
                image_bytes = b""
        else:
            image_bytes = b""

        if error is None:
            dims = png_dimensions(image_bytes)
            dims_ok = dims == (plan["width"], plan["height"])
            record["status"] = "ok" if dims_ok else "dimension_mismatch"
            record["image"] = {
                "file": png_path.name,
                "bytes": len(image_bytes),
                "sha256": sha256_bytes(image_bytes),
                "width": dims[0] if dims else None,
                "height": dims[1] if dims else None,
                "dimensions_match_canvas": dims_ok,
                "edited": False,
            }
            png_path.write_bytes(image_bytes)
            print(f"{case_id}: OK {dims[0]}x{dims[1]} {len(image_bytes)/1e6:.2f} MB "
                  f"in {total_s:.1f} s (peak {mon_summary.get('vram_peak_mb', 0):.0f} MB)")
        else:
            record["status"] = "error"
            record["error"] = error[:2000]
            hist_status = history.get("status", {})
            if hist_status:
                record["server_status"] = hist_status
            print(f"{case_id}: ERROR — {error[:200]}")

        rec_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        summary.append({
            "case_id": case_id,
            "status": record["status"],
            "total_s": record["timing"]["total_s"],
            "image_sha256": record.get("image", {}).get("sha256"),
            "width": plan["width"], "height": plan["height"],
        })

    index_path = out_dir / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session": session,
                "base_url": base_url,
                "mode": "quality (bf16, 40 steps)",
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "environment": env_block,
                "runs": summary,
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    ok = sum(1 for r in summary if r["status"] == "ok")
    print(f"\n[{ok}/{len(summary)}] cases OK — records in {out_dir}")


if __name__ == "__main__":
    main()
