# Security Policy — and the BYOK security model

## The BYOK invariant

This project is designed so that **no contributor's OpenAI API key can leak
through it**, because the project itself never possesses one:

| Rule | Enforcement |
|---|---|
| No key in any git file | `.gitignore` blocks env files; `tools/validate_gallery.py` scans every tracked text file for key-shaped patterns (`sk-…`, `OPENAI_API_KEY=…`, `Bearer …`) and fails CI on any hit; the BYOK CLI's `self_scan` refuses to write any artifact containing the in-memory key string |
| No key in logs / errors | exception text is scrubbed through `redact()` before any `HttpError` escapes `generate_image`; error bodies never echo request headers |
| No key on the website | the site is a fully static Vite build — no backend, no forms, no analytics, no storage; it never asks for or handles credentials |
| No browser calls to the model API | generation is CLI-only (`tools/generate_gpt.py`); there is no web runner in this repo, so no CORS/key-relay surface exists |
| No keys to maintainers | contributions contain images + sanitized run records only; `run.json` records the *handling policy*, never key material; the self-scan runs on every output file before the process exits |
| No keys in CI | GitHub Actions never touch the OpenAI API; BYOK tests use injected fake transports (contract tests), no network |
| No unbounded paid retries | hard cap: 1 attempt + 2 retries (429/5xx/network only, exponential backoff); 4xx user errors are never retried; default `n=1` |
| Explicit cost gate | model, size, quality, n, and estimated cost are printed before any paid request; interactive `YES` required unless `--yes` is passed explicitly |

If a localhost web runner is ever added, it must: bind 127.0.0.1 only, serve
its own frontend, enforce Origin + CSRF checks, no wildcard CORS, key read
only by the local backend — per the project's standing security gate. Until
that ships, the CLI is the only sanctioned path.

## Reporting a vulnerability

Please report privately to the repository owner via GitHub security advisories
("Security" tab → "Report a vulnerability"). Do **not** open a public issue
containing secrets, payloads, or exploitable detail. Expect a response within
a few days.

## Scope notes

- The static website has no server surface; report site issues as normal bugs.
- The engine repo ([qwen-image-rocm](https://github.com/AIwork4me/qwen-image-rocm))
  has its own security docs; this repo depends on it as an external,
  unmodified local checkout.
- Prompt-injection style risks from model outputs are out of scope: gallery
  images are treated as data, never executed, and the site renders them as
  plain `<img>` content.
