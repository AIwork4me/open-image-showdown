/**
 * Build the site data model from frozen artifacts.
 *
 * Reads:  ../cases/<id>/manifest.json, ../cases/<id>/prompt.txt
 *         ../gallery/qwen/<id>.png, ../gallery/qwen/<id>.run.json
 *         ../gallery/reference/index.json        (rights ledger, P2)
 *         ../submissions/** (community GPT submissions, reviewed only)
 * Writes: src/data/cases.json        (typed site model, prompts embedded)
 *         public/gallery/...         (copied image assets)
 *
 * Deterministic apart from built_at: same repo state -> identical output. No network, no keys.
 *
 * Evidence rules (unchanged from the first release):
 *   OPEN_CHALLENGE          no reviewed GPT submission
 *   COMMUNITY_SUBMITTED     submission received, awaiting review
 *   REVIEWED_COMPARISON     submission with review.state = "accepted"
 *   BLOCKED                 manifest.status === "BLOCKED"
 * GPT model identity is NEVER inferred from image content — only from the
 * evidence recorded in the submission record.
 *
 * Reference-image rules (gallery-first release):
 *   - A library reference image is copied into the site ONLY when its ledger
 *     record is display_permission === "APPROVED" AND mirror.sha256_verified
 *     AND the mirrored file exists on disk. Otherwise the case carries a
 *     labeled link-out card (never a placeholder image).
 *   - display_mode: VERIFIED_GPT_COMPARISON (accepted submission) beats
 *     REFERENCE_RECREATION (approved reference + real Qwen); otherwise
 *     QWEN_ONLY.
 *   - Reference images are "Community Gallery Reference — Model Unverified";
 *     they never promote a case status and are never labeled verified GPT.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = dirname(webRoot);
const casesDir = join(repoRoot, 'cases');
const galleryDir = join(repoRoot, 'gallery', 'qwen');
const referenceLedgerPath = join(repoRoot, 'gallery', 'reference', 'index.json');
const referenceImagesDir = join(repoRoot, 'gallery', 'reference', 'images');
const submissionsDir = join(repoRoot, 'submissions');
const outData = join(webRoot, 'src', 'data', 'cases.json');
const outGallery = join(webRoot, 'public', 'gallery');

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');

function readJson(p) {
  return JSON.parse(readFileSync(p, 'utf8'));
}

/** Collect reviewed/pending community GPT submissions for a case. */
function collectSubmissions(caseId) {
  const dir = join(submissionsDir, caseId);
  if (!existsSync(dir)) return [];
  const out = [];
  for (const entry of readdirSync(dir)) {
    const recPath = join(dir, entry, 'submission.json');
    if (!existsSync(recPath)) continue;
    const rec = readJson(recPath);
    const imgRel = rec.image?.file;
    if (!imgRel) continue;
    const imgAbs = join(dir, entry, imgRel);
    if (!existsSync(imgAbs)) continue;
    const dest = `submissions/${caseId}/${entry}/${imgRel}`;
    mkdirSync(join(outGallery, dirname(dest)), { recursive: true });
    copyFileSync(imgAbs, join(outGallery, dest));
    out.push({
      id: entry,
      state: rec.review?.state ?? 'pending', // pending | accepted | rejected
      image: `gallery/${dest}`,
      image_sha256: rec.image.sha256 ?? sha256(readFileSync(imgAbs)),
      submitted_by: rec.submitted_by ?? 'anonymous',
      submitted_at: rec.submitted_at ?? null,
      evidence: {
        model: rec.model ?? null,
        model_snapshot: rec.model_snapshot ?? null,
        api_evidenced: Boolean(rec.run?.usage ?? rec.usage),
        run_record_available: Boolean(rec.run),
        method: rec.method ?? 'unknown',
      },
      license_note: rec.license ?? 'contributor grants display license per contribution terms',
    });
  }
  return out;
}

/** Build the site reference-image block from a rights-ledger record.
 *  Hard gate: renderable === APPROVED && mirrored && file exists. */
function referenceBlock(rec, promptMatchOverride) {
  const mirroredRel = rec.mirror?.path;
  const mirrorAbs = mirroredRel ? join(repoRoot, mirroredRel) : null;
  const renderable =
    rec.display_permission === 'APPROVED' &&
    Boolean(rec.mirror?.sha256_verified) &&
    mirrorAbs !== null && existsSync(mirrorAbs);

  let image = null;
  if (renderable) {
    const dest = `reference/${rec.case_id}.jpg`;
    mkdirSync(join(outGallery, 'reference'), { recursive: true });
    copyFileSync(mirrorAbs, join(outGallery, dest));
    image = `gallery/${dest}`;
  }

  return {
    display_permission: rec.display_permission,
    renderable,
    image,
    image_sha256: rec.image_sha256,
    width: rec.width,
    height: rec.height,
    original_author: rec.original_author,
    original_post_url: rec.original_post_url,
    original_author_profile_url: rec.original_author_profile_url,
    library_case_url: rec.library_case_url,
    source_commit_sha: rec.source_commit_sha,
    model_identity: rec.model_identity,
    prompt_match_level: promptMatchOverride?.level ?? rec.prompt_match_level,
    prompt_match_note: promptMatchOverride?.note ?? rec.prompt_match_note,
    aspect_match: rec.aspect_match,
    aspect_disclosure_required: rec.aspect_disclosure_required,
    attribution: rec.attribution,
    reuse_restrictions: rec.reuse_restrictions,
  };
}

function build() {
  const index = readJson(join(casesDir, 'index.json'));
  const ledger = readJson(referenceLedgerPath);
  const refByCase = new Map(ledger.references.map((r) => [r.case_id, r]));
  const cases = [];

  for (const entry of index.cases) {
    const caseId = entry.case_id;
    const manifest = readJson(join(casesDir, caseId, 'manifest.json'));
    const prompt = readFileSync(join(casesDir, caseId, 'prompt.txt'), 'utf8');
    const promptSha = sha256(Buffer.from(prompt, 'utf8'));
    if (promptSha !== manifest.prompt.sha256) {
      throw new Error(`${caseId}: prompt.txt sha256 drift — refusing to build site data`);
    }

    // Qwen side (must be a real run record + image)
    const pngPath = join(galleryDir, `${caseId}.png`);
    const runPath = join(galleryDir, `${caseId}.run.json`);
    let qwen = null;
    if (existsSync(pngPath) && existsSync(runPath)) {
      const run = readJson(runPath);
      if (run.status !== 'ok') {
        throw new Error(`${caseId}: run status ${run.status} — failed runs must not ship as gallery images`);
      }
      if (run.prompt.sha256 !== manifest.prompt.sha256) {
        throw new Error(`${caseId}: run record prompt sha does not match frozen manifest`);
      }
      const dest = `qwen/${caseId}.png`;
      mkdirSync(join(outGallery, 'qwen'), { recursive: true });
      copyFileSync(pngPath, join(outGallery, dest));
      const webpDest = join(outGallery, 'qwen', `${caseId}.webp`); // committed derivative, if generated
      qwen = {
        image: `gallery/${dest}`,
        image_web: existsSync(webpDest) ? `gallery/qwen/${caseId}.webp` : null,
        image_sha256: run.image.sha256,
        width: run.image.width,
        height: run.image.height,
        generation: {
          model: 'Qwen-Image-2.1',
          weights_repo: run.environment.weights_repo,
          weights_revision: run.environment.weights_revision,
          comfyui_commit: run.environment.comfyui_commit,
          engine_repo: run.environment.engine_repo,
          engine_commit: run.environment.engine_commit,
          gpu: 'AMD Radeon RX 7900 XTX 24 GB (gfx1100, native Windows ROCm)',
          precision: 'bf16',
          steps: run.params.steps,
          cfg: run.params.cfg,
          sampler: `${run.params.sampler}/${run.params.scheduler}`,
          seed: run.params.seed,
          size: `${run.params.width}x${run.params.height}`,
          wall_time_s: run.timing.total_s,
          vram_peak_mb: run.monitor?.vram_peak_mb ?? null,
          generated_utc: run.finished_utc,
          non_square_probe: run.params.width !== run.params.height,
        },
        license: 'CC BY-NC 4.0 (generated with Qwen-Image-2.1 under the Qwen Research License)',
      };
    }

    // Reference-image block (rights-gated). Variant cases (case-390t) reuse
    // their parent case's reference record — the permission covers the IMAGE
    // — with their own prompt-match note.
    let referenceImage = null;
    const parentCaseId = manifest.variant_of ?? entry.variant_of ?? null;
    if (parentCaseId && refByCase.has(parentCaseId)) {
      referenceImage = referenceBlock(refByCase.get(parentCaseId), {
        level: 'DERIVED_TEMPLATE_FILL',
        note:
          `variant pairing: upstream template resolved to '${manifest.prompt.derivation?.value}' ` +
          '(parameter inferred from the reference image content, not author-confirmed)',
      });
    } else if (refByCase.has(caseId)) {
      referenceImage = referenceBlock(refByCase.get(caseId));
    } else if (!parentCaseId) {
      throw new Error(`${caseId}: no rights-ledger record for primary case`);
    }

    const submissions = collectSubmissions(caseId);
    const accepted = submissions.filter((s) => s.state === 'accepted');
    const pending = submissions.filter((s) => s.state === 'pending');

    let status;
    if (manifest.status === 'BLOCKED') status = 'BLOCKED';
    else if (accepted.length > 0) status = 'REVIEWED_COMPARISON';
    else if (pending.length > 0) status = 'COMMUNITY_SUBMITTED';
    else status = 'OPEN_CHALLENGE';

    const displayMode = accepted.length > 0
      ? 'VERIFIED_GPT_COMPARISON'
      : referenceImage?.renderable && qwen
        ? 'REFERENCE_RECREATION'
        : 'QWEN_ONLY';

    cases.push({
      case_id: caseId,
      status,
      display_mode: displayMode,
      variant_of: manifest.variant_of ?? entry.variant_of ?? null,
      variant_kind: manifest.variant_kind ?? null,
      blocked_reason: manifest.blocked_reason,
      title: manifest.title,
      category: manifest.category,
      aspect: manifest.canvas.aspect_ratio,
      canvas: { width: manifest.canvas.width, height: manifest.canvas.height },
      prompt,
      prompt_sha256: promptSha,
      prompt_language: manifest.prompt.language,
      prompt_derivation: manifest.prompt.derivation,
      reference: manifest.reference,
      reference_image: referenceImage,
      notes: manifest.notes,
      qwen,
      gpt: {
        planned_size: `${manifest.canvas.width}x${manifest.canvas.height}`,
        planned_quality: manifest.gpt_plan.quality ?? 'medium',
        model: manifest.gpt_plan.model,
        byok: true,
        submissions: accepted.length + pending.length,
      },
      submissions,
    });
  }

  const primary = cases.filter((c) => !c.variant_of);
  const reviewed = cases.filter((c) => c.status === 'REVIEWED_COMPARISON').length;
  const approvedRefs = ledger.references.filter((r) => r.display_permission === 'APPROVED');
  const pairingsReady = cases.filter(
    (c) => !c.variant_of && c.reference_image?.renderable && c.qwen
  ).length;
  const model = {
    schema_version: 1,
    built_at: new Date().toISOString().slice(0, 19) + 'Z',
    project: 'open-image-showdown',
    tagline: 'Same Prompt. Two Models. You Decide.',
    totals: {
      cases: primary.length,
      variants: cases.length - primary.length,
      qwen_generated: cases.filter((c) => c.qwen).length,
      open_challenges: cases.filter((c) => c.status === 'OPEN_CHALLENGE').length,
      community_submitted: cases.filter((c) => c.status === 'COMMUNITY_SUBMITTED').length,
      reviewed_comparisons: reviewed,
      blocked: cases.filter((c) => c.status === 'BLOCKED').length,
      references_total: ledger.references.length,
      references_approved: approvedRefs.length,
      reference_pairings_ready: pairingsReady,
    },
    cases,
  };
  mkdirSync(dirname(outData), { recursive: true });
  writeFileSync(outData, JSON.stringify(model, null, 2) + '\n');
  console.log(
    `site data: ${primary.length} primary + ${model.totals.variants} variant cases, ` +
      `${model.totals.qwen_generated} qwen images, ` +
      `${model.totals.references_approved}/${model.totals.references_total} references renderable, ` +
      `${reviewed} reviewed comparisons -> ${relative(repoRoot, outData)}`
  );
}

build();
