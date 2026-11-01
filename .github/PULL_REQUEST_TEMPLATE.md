## What this PR does

<!-- One or two sentences. -->

## Type

- [ ] GPT submission (adds `submissions/...` — review.state stays `pending`)
- [ ] New case(s) (frozen manifest + prompt.txt via `tools/build_cases.py`)
- [ ] Qwen re-run (new `gallery/` records — old records untouched)
- [ ] Project code / site / docs
- [ ] CI / tooling

## The gate (check all — CI runs them too)

- [ ] `uv run --no-project --with pytest --python 3.12 python -I -m pytest tests/ -q` passes
- [ ] `uv run --no-project --python 3.12 python -I tools/validate_gallery.py` → PASS
- [ ] `cd web && npm ci && npm run build` passes
- [ ] No secrets, no API keys, no `.env` anywhere in this PR
- [ ] No edits to frozen `cases/*/prompt.txt` or existing `gallery/**` records
- [ ] No model weights or upstream-library images added

## Notes for reviewers

<!-- For submissions: which case, which tier (API-evidenced / self-reported), anything unusual. -->
