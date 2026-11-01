name: 🎨 GPT Image 2 submission (BYOK)
description: Submit your GPT Image 2 result for a case — bring your own key, attach your evidence
title: "[GPT] case-<id> — <your handle>"
labels: ["gpt-submission"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for contributing the GPT side! Easiest path:

        ```
        export OPENAI_API_KEY=sk-...   # your key, environment only
        uv run --no-project python -I tools/generate_gpt.py --case case-<id>
        ```

        …then attach `image.png` below and paste `SUBMISSION.md` + `run.json`.
        **Never paste your API key anywhere in this issue.**

  - type: input
    id: case_id
    attributes:
      label: Case ID
      description: Which case is this for? (e.g. case-443)
      placeholder: case-443
    validations:
      required: true

  - type: input
    id: model
    attributes:
      label: Model ID
      description: Must be a gpt-image-2 snapshot (pinned default gpt-image-2-2026-04-21)
      placeholder: gpt-image-2-2026-04-21
    validations:
      required: true

  - type: input
    id: prompt_sha
    attributes:
      label: Original Prompt SHA256
      description: From your run (SUBMISSION.md quotes it), or `sha256sum cases/<id>/prompt.txt`
      placeholder: 4087…
    validations:
      required: true

  - type: textarea
    id: params
    attributes:
      label: Generation parameters
      description: size, quality, n, output format — as run
      placeholder: "size 832x1248, quality medium, n=1, png"
    validations:
      required: true

  - type: checkboxes
    id: attachment
    attributes:
      label: Output image
      options:
        - label: I attached the unedited output image to this issue
          required: true

  - type: textarea
    id: source
    attributes:
      label: Source information / run record
      description: Paste SUBMISSION.md and run.json (sanitized) if you used the CLI; otherwise describe exactly how the image was produced
    validations:
      required: true

  - type: checkboxes
    id: rights
    attributes:
      label: Rights declaration
      options:
        - label: I generated this image myself with my own OpenAI access and have the right to submit it; I grant this project a non-exclusive, worldwide, royalty-free license to display and distribute it with attribution.
          required: true

  - type: textarea
    id: runlog
    attributes:
      label: Optional run log
      description: Terminal output of the CLI run (redacted) — helps the API-evidenced tier

  - type: input
    id: reproduce
    attributes:
      label: Reproduction method
      placeholder: tools/generate_gpt.py (repo CLI) / ChatGPT web UI / other client (describe)
    validations:
      required: true
