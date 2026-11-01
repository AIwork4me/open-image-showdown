name: 💡 Prompt suggestion
description: Suggest a new prompt/case for the showdown
title: "[prompt] <short title>"
labels: ["prompt-suggestion"]
body:
  - type: markdown
    attributes:
      value: |
        Good showdown prompts: pure text-to-image (no reference images), stress
        text rendering / layout / photorealism / style, and are yours to share
        (or from a source that permits resharing with attribution).

  - type: textarea
    id: prompt
    attributes:
      label: Full prompt text
    validations:
      required: true

  - type: input
    id: source
    attributes:
      label: Source / attribution
      description: Yourself (say so), or a public link if republishing

  - type: dropdown
    id: axis
    attributes:
      label: What does it stress?
      options:
        - Typography / text rendering
        - Layout / infographic structure
        - Photorealism
        - Style / illustration
        - Multi-panel consistency
        - Other
    validations:
      required: true

  - type: input
    id: aspect
    attributes:
      label: Intended aspect ratio
      placeholder: "9:16 / 1:1 / 16:9 / A4 portrait"

  - type: checkboxes
    id: rights
    attributes:
      label: Sharing rights
      options:
        - label: The prompt is mine to share, or its source permits resharing with attribution (MIT-compatible)
          required: true
