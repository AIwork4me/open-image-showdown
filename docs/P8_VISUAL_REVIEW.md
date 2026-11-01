# P8 — Independent Visual Review (Gallery-First Release)

Review date: 2026-11-01 · Method: real browser sessions (ZCode in-app browser, Playwright-driven)
against the production Vite build (`vite preview`) and the pushed branch as rendered by GitHub.
Every item below was verified from an actual screenshot (evidence in
[docs/screenshots/gallery-first/](screenshots/gallery-first/)), plus programmatic checks
(broken-image scan, overflow measurement) in the same sessions. No check was replaced by
schema/CI output.

## Verdict: PASS (after one real fix)

One genuine mobile defect was found and fixed during the review (see §3). Everything else passed
on first render.

## 1. README on GitHub (branch `feat/gallery-first-release`)

| Check | Result | Evidence |
|---|---|---|
| First screen: `# GPT Image 2 vs Qwen-Image 2.1` + `Same Prompt. Two Models. You Decide.` + dynamic count line | ✅ renders exactly, count line reflects `0/12` ledger truth | `readme-desktop-top.png` |
| Hero pair #443: two-column HTML table — left = labeled reference badges (view-at-library / author / mirror-pending), right = real Qwen taco image | ✅ table renders, badges clickable, image large and complete | `readme-desktop-hero443.png` |
| All images resolve (relative paths from branch) | ✅ 26–35 imgs, **0 broken** (programmatic) | session log |
| Mobile 390px | ✅ no horizontal page overflow (GitHub's responsive container), no broken images | `readme-mobile-390.png` |

## 2. Website (production build)

| Check | Result | Evidence |
|---|---|---|
| Home first screen: title → tagline → count line → **hero pair** (reference link-out card + real Qwen image) → CTAs → stats | ✅ exact hierarchy; link-out card clearly labeled "MODEL UNVERIFIED · author permission pending" with two working buttons; **no fake reference image** | `web-home-desktop.png` |
| Case grid: dual-thumb cards — left reference half = dashed pending panel with label, right = Qwen image with `contain` (no cropping of in-image text) | ✅ taco labels / exam text / recipe steps all fully visible; corner labels readable | `web-case-grid-desktop.png` |
| Case pages: two display-mode sections (Gallery Reference vs Qwen Recreation / Verified GPT vs Qwen empty slot), aspect-disclosure callouts, variant crosslinks | ✅ verified on case-443 (aspect note present), case-390 + case-390t (variant notes both directions), case-13, case-419 | `web-case-390-desktop.png` |
| Slider policy | ✅ no drag-slider anywhere references aren't renderable (aspect-mismatched or pending) — programmatic `hasSlider=false` on all five checked pages | session log |
| Copy prompt interaction | ✅ click → "✓ Copied" feedback (polled in-session) | session log |
| Full-resolution links, sha chips, source/rights table | ✅ present on all checked case pages | session log |
| Broken images | ✅ 0 across home + 5 case pages (programmatic) | session log |

## 3. Defect found & fixed during review

**Mobile horizontal overflow on case pages (real bug, pre-existing from the first release,
exposed by this review):** at 375px, `.detail-grid` grid tracks sized to the intrinsic width of
the long `<pre>` prompt/reproduce lines (547px > 375px viewport). Fixed by allowing grid children
to shrink (`min-width: 0; max-width: 100%` + `pre { max-width: 100%; overflow-x: auto }`) in
`web/src/styles/global.css`. Re-verified in-session after rebuild: `scrollWidth 375 == viewport
375`. Evidence: `web-case-443-mobile-390-fixed.png` (post-fix, with aspect-disclosure note and
reference link-out visible).

## 4. Social cards (spot-checked visually during generation)

- case card: left status panel clearly labeled, never a stand-in image; right Qwen image complete;
  title/subtitle/attribution readable — after two generator fixes (bottom-bar overlap, heading
  fit) that were made *before* commit.
- project card: pills and footer fully inside the dark panel — after a layout rework.
- Both fixes are guarded structurally (`fit_font` shrink-to-fit loops) and by
  `test_social_card_reference_policy`.

## 5. Review limitations (stated honestly)

- GitHub Pages is not yet enabled (owner action), so the *deployed* site was not reviewed — the
  review ran against the production build served locally (`vite preview`, same bytes CI builds).
- Reference-image side-by-side rendering could not be visually exercised because no reference is
  rights-APPROVED yet; the renderable path is covered by unit tests
  (`test_display_modes_are_evidence_consistent`, `ref_state`) and activates via the ledger the
  moment an approval lands.
- Screens were captured at 1440×900, 390×844 (CSS 375), plus 640px-class media queries exercised
  via CSS review; 430px was not separately screenshotted (same breakpoint bucket as 390).
