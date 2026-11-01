# Contributing to Open Image Showdown

Thanks for helping build an honest, verifiable image-model comparison. This
project's core asset is **trust**: every image has provenance, every claim has
a record. Contributions that strengthen that are welcome; anything that
weakens it will be declined.

## The three ways to contribute

### 1. Submit a GPT Image 2 result (BYOK) — the main event

You need: your own OpenAI API key, Python 3.12+, `uv`, git.

```bash
export OPENAI_API_KEY=sk-...   # your key, environment only
uv run --no-project python -I tools/generate_gpt.py --case case-443
```

The CLI shows model/size/quality/**estimated cost** and waits for `YES`
(skip only with `--yes`). It writes `image.png`, `run.json` (sanitized), and a
pre-filled `SUBMISSION.md` into `contributions/<case>/gpt-run-<ts>/`.

Then either:
- **Issue**: [open a GPT submission issue](https://github.com/AIwork4me/open-image-showdown/issues/new?template=gpt_submission.md),
  attach the image, paste `SUBMISSION.md` + `run.json` contents.
- **PR** (preferred): add `submissions/<case>/<your-handle>/` containing
  `submission.json`, the image, and `run.json` (see the schema below).

#### Manual upload (generated elsewhere)

If you made the image in ChatGPT or another client, use the same issue
template and say so. Your submission will be labeled **self-reported** rather
than API-evidenced — same display treatment, honestly tiered. Bare images
with no statement of origin cannot be accepted.

#### submission.json (PR path)

```json
{
  "schema_version": 1,
  "case_id": "case-443",
  "submitted_by": "your-handle",
  "submitted_at": "2026-11-01T12:00:00Z",
  "model": "gpt-image-2",
  "model_snapshot": "gpt-image-2-2026-04-21",
  "method": "tools/generate_gpt.py (BYOK) | manual upload (ChatGPT web UI) | ...",
  "image": { "file": "image.png", "sha256": "<hex>" },
  "usage": { "the api usage object from run.json if present": "..." },
  "run": { "...": "contents (or summary) of run.json" },
  "review": { "state": "pending" },
  "license": "contributor grants the project a non-exclusive, worldwide, royalty-free license to display and distribute this submission with attribution (CC BY 4.0 display)"
}
```

`review.state` stays `pending` — maintainers set it to `accepted`/`rejected`
during review (see [docs/METHODOLOGY.md](docs/METHODOLOGY.md)).

### 2. Suggest a new prompt

[Open a prompt suggestion](https://github.com/AIwork4me/open-image-showdown/issues/new?template=prompt_suggestion.md).
Requirements: pure text-to-image (no reference images), you may share the
prompt text under MIT, and ideally a public source link. Good suggestions
stress text rendering, layout, photorealism, or style — the axes this
showdown measures.

### 3. Improve the project itself

Code, site, validation, docs — normal PRs. Run the gate locally first:

```bash
uv run --no-project --with pytest --python 3.12 python -I -m pytest tests/ -q
uv run --no-project --python 3.12 python -I tools/validate_gallery.py
cd web && npm ci && npm run build
```

## Hard rules (PR-blocking)

1. **Never commit secrets.** No API keys, tokens, or `.env` files. The
   validator scans every text file for key-shaped strings.
2. **Never edit frozen prompts or pasted run records.** `cases/*/prompt.txt`
   and `gallery/**` are immutable history. Changes require a new case id or a
   documented re-run.
3. **Never relabel model identity.** GPT images only via their evidence tier;
   never mark anything `REVIEWED_COMPARISON` in your own PR — that's the
   maintainer review gate.
4. **No model weights** (or pieces of them) in this repo, ever.
5. **No upstream library images.** Prompt text (MIT) only, with attribution.

## Recognition

Contributors are credited in the case page and `SUBMISSION.md` of their
run (`submitted_by`). Review status is always visible.

## Questions

Open an issue with the `question` label. For security matters see
[docs/SECURITY.md](docs/SECURITY.md) — do not post keys or secrets in issues.
