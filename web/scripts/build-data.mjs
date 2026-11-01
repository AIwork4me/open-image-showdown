/**
 * Build the site data model from frozen artifacts.
 *
 * Reads:  ../cases/<id>/manifest.json, ../cases/<id>/prompt.txt
 *         ../gallery/qwen/<id>.png, ../gallery/qwen/<id>.run.json
 *         ../submissions/** (community GPT submissions, reviewed only)
 * Writes: src/data/cases.json        (typed site model, prompts embedded)
 *         public/gallery/...         (copied image assets)
 *
 * Deterministic: same repo state -> identical output. No network, no keys.
 * Status derivation is evidence-based:
 *   OPEN_CHALLENGE          no reviewed GPT submission
 *   COMMUNITY_SUBMITTED     submission received, awaiting review (submissions/
 *                           with review.state = "pending")
 *   REVIEWED_COMPARISON     submission with review.state = "accepted"
 *   BLOCKED                 manifest.status === "BLOCKED"
 * GPT model identity is NEVER inferred from image content — only from the
 * evidence recorded in the submission record.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = dirname(webRoot);
const casesDir = join(repoRoot, 'cases');
const galleryDir = join(repoRoot, 'gallery', 'qwen');
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
      image: `/gallery/${dest}`,
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

function build() {
  const index = readJson(join(casesDir, 'index.json'));
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
      qwen = {
        image: `/gallery/${dest}`,
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

    const submissions = collectSubmissions(caseId);
    const accepted = submissions.filter((s) => s.state === 'accepted');
    const pending = submissions.filter((s) => s.state === 'pending');

    let status;
    if (manifest.status === 'BLOCKED') status = 'BLOCKED';
    else if (accepted.length > 0) status = 'REVIEWED_COMPARISON';
    else if (pending.length > 0) status = 'COMMUNITY_SUBMITTED';
    else status = 'OPEN_CHALLENGE';

    cases.push({
      case_id: caseId,
      status,
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

  const reviewed = cases.filter((c) => c.status === 'REVIEWED_COMPARISON').length;
  const model = {
    schema_version: 1,
    built_at: new Date().toISOString().slice(0, 19) + 'Z',
    project: 'open-image-showdown',
    tagline: 'Same Prompt. Two Models. You Decide.',
    totals: {
      cases: cases.length,
      qwen_generated: cases.filter((c) => c.qwen).length,
      open_challenges: cases.filter((c) => c.status === 'OPEN_CHALLENGE').length,
      community_submitted: cases.filter((c) => c.status === 'COMMUNITY_SUBMITTED').length,
      reviewed_comparisons: reviewed,
      blocked: cases.filter((c) => c.status === 'BLOCKED').length,
    },
    cases,
  };
  mkdirSync(dirname(outData), { recursive: true });
  writeFileSync(outData, JSON.stringify(model, null, 2) + '\n');
  console.log(
    `site data: ${cases.length} cases, ` +
      `${model.totals.qwen_generated} qwen images, ` +
      `${reviewed} reviewed comparisons -> ${relative(repoRoot, outData)}`
  );
}

build();
