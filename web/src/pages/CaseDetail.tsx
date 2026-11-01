import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { siteModel, repoUrl, asset } from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import PromptBlock from '../components/PromptBlock';
import Lightbox from '../components/Lightbox';
import CompareSlider from '../components/CompareSlider';
import ReferencePanel from '../components/ReferencePanel';
import type { Case } from '../types';

function fmtSeconds(s: number) {
  return `${s.toFixed(1)} s`;
}

/** Two images may use the drag-slider only when their aspect ratios match
 *  (within 2%) — otherwise information near edges would be hidden. */
function aspectRatioClose(a: { width: number; height: number }, b: { width: number; height: number }) {
  const ra = a.width / a.height;
  const rb = b.width / b.height;
  return Math.abs(ra - rb) / rb < 0.02;
}

export default function CaseDetail() {
  const { caseId } = useParams();
  const [lightbox, setLightbox] = useState<{ src: string; cap: string } | null>(null);
  const [useSlider, setUseSlider] = useState(false);
  // Blind A/B: randomize which side renders left, decided once per case view.
  const [blindFlip] = useState(() => Math.random() < 0.5);
  const c: Case | undefined = siteModel.cases.find((x) => x.case_id === caseId);

  if (!c) {
    return (
      <div className="not-found container">
        <h1>Case not found</h1>
        <p>
          <a href="#/">← back to all challenges</a>
        </p>
      </div>
    );
  }

  const accepted = c.submissions.filter((s) => s.state === 'accepted');
  const gpt = accepted[0] ?? null; // first reviewed submission
  const shareUrl = `${window.location.origin}${window.location.pathname}#/case/${c.case_id}`;
  const ri = c.reference_image;
  const variant = siteModel.cases.find((v) => v.variant_of === c.case_id);
  const parent = c.variant_of ? siteModel.cases.find((p) => p.case_id === c.variant_of) : null;
  const sliderAllowed =
    !!ri?.renderable && !!c.qwen && aspectRatioClose(ri, c.qwen) && !ri.aspect_disclosure_required;

  const gptPanel = gpt ? (
    <div className="panel side-openai">
      <div className="panel-head">
        GPT Image 2 <span className="sub">verified · {gpt.evidence.model_snapshot ?? gpt.evidence.model}</span>
      </div>
      <div className="img-holder">
        <img
          src={asset(gpt.image)}
          alt={`${c.title.en} — GPT Image 2 output`}
          onClick={() => setLightbox({ src: asset(gpt.image), cap: `${c.title.en} — GPT Image 2 (reviewed submission)` })}
        />
      </div>
      <div className="panel-foot">
        <span className="chip">sha256 {gpt.image_sha256.slice(0, 10)}…</span>
        <span className="chip">{gpt.evidence.api_evidenced ? 'API-evidenced' : 'self-reported'}</span>
        <span className="chip">by {gpt.submitted_by}</span>
      </div>
    </div>
  ) : (
    <div className="panel side-openai">
      <div className="panel-head">
        Verified GPT Image 2
        <span className="sub">model: {c.gpt.model}</span>
      </div>
      <div className="pending-slot">
        <span className="badge open">
          <span className="dot" />
          Community submission pending
        </span>
        <div>
          <p className="big">No verified GPT Image 2 result exists for this case yet.</p>
          <p>
            This slot stays empty on purpose — it will never hold a placeholder, a library image,
            or any image of unverified origin. The community gallery reference above is a separate,
            clearly-labeled thing and never counts as the GPT side.
          </p>
          <a className="btn primary" href="#/contribute">
            Generate it with your key →
          </a>
        </div>
      </div>
      <div className="panel-foot">
        <span className="chip">planned size {c.gpt.planned_size}</span>
        <span className="chip">BYOK</span>
      </div>
    </div>
  );

  const qwenPanel = c.qwen ? (
    <div className="panel side-qwen">
      <div className="panel-head">
        Qwen-Image 2.1
        <span className="sub">
          bf16 · {c.qwen.generation.steps} steps · seed {c.qwen.generation.seed}
        </span>
      </div>
      <div className="img-holder">
        <img
          src={asset(c.qwen.image_web ?? c.qwen.image)}
          alt={`${c.title.en} — Qwen-Image 2.1 output`}
          onClick={() => setLightbox({ src: asset(c.qwen!.image), cap: `${c.title.en} — Qwen-Image 2.1` })}
        />
      </div>
      <div className="panel-foot">
        <span className="chip">{c.qwen.generation.size}</span>
        <span className="chip">{fmtSeconds(c.qwen.generation.wall_time_s)} wall</span>
        <span className="chip">RX 7900 XTX · ROCm</span>
        <span className="chip mono" title={c.qwen.image_sha256}>
          sha {c.qwen.image_sha256.slice(0, 10)}…
        </span>
        <span className="chip link-chip">
          <a href={asset(c.qwen.image)} target="_blank" rel="noreferrer">
            full resolution ↗
          </a>
        </span>
      </div>
    </div>
  ) : (
    <div className="panel side-qwen">
      <div className="panel-head">Qwen-Image 2.1</div>
      <div className="pending-slot">
        <p className="big">Generation failed or not yet run.</p>
        <p>
          Failures are reported honestly — see{' '}
          <a href={`${repoUrl}/blob/main/docs/QWEN_12_CASE_RESULTS.md`}>
            docs/QWEN_12_CASE_RESULTS.md
          </a>
          .
        </p>
      </div>
    </div>
  );

  const [leftPanel, rightPanel] = blindFlip && gpt && c.qwen ? [qwenPanel, gptPanel] : [gptPanel, qwenPanel];

  const derivationNote = useMemo(
    () =>
      c.prompt_derivation ? (
        <div className="callout warn" style={{ marginTop: 14 }}>
          <b>Derived prompt (recorded).</b> The upstream prompt contained the template variable{' '}
          <code>{c.prompt_derivation.variable}</code>; it was resolved to{' '}
          <b>{c.prompt_derivation.value}</b> before freezing. Upstream prompt sha256:{' '}
          <span className="mono">{c.prompt_derivation.upstream_prompt_sha256.slice(0, 16)}…</span>
        </div>
      ) : null,
    [c.prompt_derivation]
  );

  return (
    <main>
      <div className="container case-hero">
        <a className="back" href="#/">
          ← all comparisons
        </a>
        <h1>{c.title.en}</h1>
        <p className="zh">{c.title.zh}</p>
        <div className="badges">
          <StatusBadge status={c.status} />
          <span className="chip">{c.category}</span>
          <span className="chip">{c.aspect}</span>
          <span className="chip">
            canvas {c.canvas.width}×{c.canvas.height}
          </span>
          {c.prompt_derivation && <span className="chip">derived prompt</span>}
          {c.variant_of && <span className="chip">reference-pairing variant of #{c.variant_of.replace('case-', '')}</span>}
        </div>
        {c.blocked_reason && (
          <div className="callout warn" style={{ marginTop: 12 }}>
            <b>Blocked:</b> {c.blocked_reason}
          </div>
        )}
      </div>

      {/* ---- Display mode 1 (default): Gallery Reference vs Qwen Recreation ---- */}
      <div className="container compare-wrap">
        <div className="section-head">
          <h2 className="small">Gallery Reference vs Qwen Recreation</h2>
          {ri && (
            <span className="count">
              prompt match: <b>{ri.prompt_match_level === 'EXACT' ? 'exact' : 'derived (recorded)'}</b>
              {sliderAllowed && (
                <>
                  {' '}·
                  <button className="link chip" onClick={() => setUseSlider(!useSlider)}>
                    {useSlider ? 'side-by-side view' : 'slider view'}
                  </button>
                </>
              )}
            </span>
          )}
        </div>

        {useSlider && sliderAllowed && ri?.renderable && c.qwen ? (
          <>
            <CompareSlider
              leftSrc={asset(ri.image!)}
              rightSrc={asset(c.qwen.image)}
              leftLabel="Reference · unverified"
              rightLabel="Qwen 2.1"
              alt={c.title.en}
            />
            <div className="compare-grid" style={{ marginTop: 14 }}>
              <ReferencePanel c={c} onZoom={(s, cap) => setLightbox({ src: s, cap })} />
              {qwenPanel}
            </div>
          </>
        ) : (
          <div className="compare-grid">
            <ReferencePanel c={c} onZoom={(s, cap) => setLightbox({ src: s, cap })} />
            {qwenPanel}
          </div>
        )}

        {ri?.aspect_disclosure_required && c.qwen && (
          <div className="callout" style={{ marginTop: 14 }}>
            <b>Different canvases — nothing is cropped.</b> The community reference is {ri.width}×{ri.height} (
            {(ri.width / ri.height).toFixed(3)} ratio); this Qwen canvas is {c.qwen.width}×{c.qwen.height} (
            {(c.qwen.width / c.qwen.height).toFixed(3)} ratio). The two images were generated on different
            canvas shapes, so each is shown complete at its own ratio (letterboxed where needed) — this is
            not a same-canvas A/B.
          </div>
        )}
        {ri?.prompt_match_level === 'DERIVED_TEMPLATE_FILL' && !c.variant_of && (
          <div className="callout warn" style={{ marginTop: 12 }}>
            <b>Not an exact-prompt pairing.</b> The frozen prompt resolves an upstream template variable
            differently from what the reference image depicts — see the derivation note below and the{' '}
            <a href={`${repoUrl}/blob/main/docs/REFERENCE_IMAGE_AUDIT.md#6-case-390-remediation-critical-case-fix`}>
              audit's remediation
            </a>
            .
          </div>
        )}
        {variant && (
          <div className="callout" style={{ marginTop: 12 }}>
            <b>Exact-prompt variant available.</b> The reference depicts a different value of the template
            variable than the frozen prompt;{' '}
            <a href={`#/case/${variant.case_id}`}>
              {variant.title.en} (#{variant.case_id.replace('case-', '')})
            </a>{' '}
            re-runs the same upstream template with the inferred parameter for a true exact-prompt pairing.
          </div>
        )}
        {parent && (
          <div className="callout" style={{ marginTop: 12 }}>
            <b>Variant case.</b> This is a reference-pairing variant of{' '}
            <a href={`#/case/${parent.case_id}`}>#{parent.case_id.replace('case-', '')}</a> — the primary frozen
            case and its run record are unchanged. The parameter that differs (here: the country) was inferred
            from the reference image's content, <b>not</b> confirmed by the original author.
          </div>
        )}
      </div>

      {/* ---- Display mode 2: Verified GPT Image 2 vs Qwen (review-gated) ---- */}
      <div className="container compare-wrap">
        <div className="section-head">
          <h2 className="small">Verified GPT Image 2 vs Qwen</h2>
          <span className="count">
            {gpt ? 'reviewed community submission — real comparison' : 'empty until a reviewed submission exists'}
          </span>
        </div>
        {gpt && c.qwen ? (
          <>
            <CompareSlider
              leftSrc={asset(blindFlip ? c.qwen.image : gpt.image)}
              rightSrc={asset(blindFlip ? gpt.image : c.qwen.image)}
              leftLabel={blindFlip ? 'B' : 'A'}
              rightLabel={blindFlip ? 'A' : 'B'}
              alt={c.title.en}
            />
            <p className="blind-note">
              Sides are labeled <b>A / B</b> and randomized on each visit — future blind-rating flows build on
              this. Which is which? Check the run metadata below after you judge.
            </p>
            <div className="compare-grid" style={{ marginTop: 14 }}>
              {leftPanel}
              {rightPanel}
            </div>
          </>
        ) : (
          <div className="compare-grid">
            {gptPanel}
            {qwenPanel}
          </div>
        )}
      </div>

      <div className="container detail-grid" style={{ marginTop: 26 }}>
        <div>
          <PromptBlock prompt={c.prompt} sha256={c.prompt_sha256} language={c.prompt_language} />
          {derivationNote}
          <div style={{ marginTop: 16 }}>
            <div className="callout">
              <b>Reproduce this case</b>
              <pre style={{ margin: '10px 0 0', fontFamily: 'var(--mono)', fontSize: 12.3, overflow: 'auto' }}>
{`# GPT side — your key, your machine (est. cost shown before confirm)
uv run --no-project python -I tools/generate_gpt.py --case ${c.case_id}

# Qwen side — RX 7900 XTX + the qwen-image-rocm engine
# see docs/QWEN_12_CASE_RESULTS.md for the exact run record`}
              </pre>
            </div>
          </div>
          {c.notes.length > 0 && (
            <div className="callout" style={{ marginTop: 16 }}>
              <b>Case notes</b>
              <ul style={{ margin: '8px 0 0', paddingLeft: 18, color: 'var(--text-dim)', fontSize: 13.5 }}>
                {c.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <aside>
          <div className="prompt-block" style={{ marginBottom: 16 }}>
            <div className="head">
              <b>Run metadata</b>
            </div>
            <div style={{ padding: '12px 16px' }}>
              <table className="meta-table">
                <tbody>
                  {c.qwen ? (
                    <>
                      <tr>
                        <th>Qwen model</th>
                        <td>
                          Qwen-Image-2.1 (bf16)<br />
                          <code>
                            {c.qwen.generation.weights_repo}@{c.qwen.generation.weights_revision.slice(0, 7)}
                          </code>
                        </td>
                      </tr>
                      <tr>
                        <th>Sampler</th>
                        <td>
                          {c.qwen.generation.sampler} · {c.qwen.generation.steps} steps · cfg{' '}
                          {c.qwen.generation.cfg} · seed {c.qwen.generation.seed}
                        </td>
                      </tr>
                      <tr>
                        <th>Wall time</th>
                        <td>
                          {fmtSeconds(c.qwen.generation.wall_time_s)}
                          {c.qwen.generation.vram_peak_mb
                            ? ` · peak ${(c.qwen.generation.vram_peak_mb / 1024).toFixed(1)} GB VRAM`
                            : ''}
                        </td>
                      </tr>
                      <tr>
                        <th>Engine</th>
                        <td>
                          <code>{c.qwen.generation.engine_repo}</code>
                          <br />
                          <code>comfyui@{c.qwen.generation.comfyui_commit.slice(0, 7)}</code>
                        </td>
                      </tr>
                      <tr>
                        <th>Image license</th>
                        <td>{c.qwen.license}</td>
                      </tr>
                    </>
                  ) : (
                    <tr>
                      <th>Qwen side</th>
                      <td className="muted">no successful run recorded</td>
                    </tr>
                  )}
                  <tr>
                    <th>GPT plan</th>
                    <td>
                      {c.gpt.model}
                      <br />
                      size {c.gpt.planned_size} · quality {c.gpt.planned_quality}
                      <br />
                      <span className="muted">community BYOK run</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="prompt-block">
            <div className="head">
              <b>Source &amp; rights</b>
            </div>
            <div style={{ padding: '12px 16px' }}>
              <table className="meta-table">
                <tbody>
                  <tr>
                    <th>Prompt library</th>
                    <td>
                      <a href={c.reference.library_url}>{c.reference.library}</a> ({c.reference.library_license}) ·{' '}
                      <a href={ri?.library_case_url ?? c.reference.library_url}>
                        case #{c.reference.library_case_id}
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th>Original author</th>
                    <td>
                      {c.reference.source_label ?? 'unknown'}
                      {c.reference.source_url && (
                        <>
                          {' '}
                          · <a href={c.reference.source_url}>source post</a>
                        </>
                      )}
                    </td>
                  </tr>
                  {ri && (
                    <>
                      <tr>
                        <th>Reference image</th>
                        <td>
                          {ri.renderable ? (
                            <>
                              mirrored with permission · {ri.width}×{ri.height}
                            </>
                          ) : (
                            <>
                              <span className="muted">not mirrored — {ri.display_permission}</span>
                              <br />
                              <a href={ri.library_case_url}>view at library (pinned commit) ↗</a>
                            </>
                          )}
                          <br />
                          <span className="muted">model identity: {ri.model_identity}</span>
                        </td>
                      </tr>
                      <tr>
                        <th>Prompt correspondence</th>
                        <td>
                          {ri.prompt_match_level === 'EXACT'
                            ? 'exact — frozen prompt byte-identical to upstream'
                            : 'derived — template variable resolved before freeze (recorded)'}
                        </td>
                      </tr>
                      <tr>
                        <th>Rights / reuse</th>
                        <td>{ri.reuse_restrictions}</td>
                      </tr>
                    </>
                  )}
                  <tr>
                    <th>Reuse scope</th>
                    <td>{c.reference.source_note}</td>
                  </tr>
                  <tr>
                    <th>Share this case</th>
                    <td>
                      <code>{shareUrl}</code>
                      <br />
                      <a href={asset(`social/${c.case_id}.png`)} target="_blank" rel="noreferrer">
                        1200×630 social preview image →
                      </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </aside>
      </div>

      {lightbox && (
        <Lightbox src={lightbox.src} caption={lightbox.cap} onClose={() => setLightbox(null)} />
      )}
    </main>
  );
}
