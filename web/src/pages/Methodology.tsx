import { siteModel, repoUrl } from '../components/Layout';

export default function Methodology() {
  return (
    <main>
      <section className="hero" style={{ paddingBottom: 10 }}>
        <div className="container">
          <span className="kicker">
            <span className="dot" />
            Methodology
          </span>
          <h1>
            Evidence over <span className="side-b">vibes</span>
          </h1>
          <p className="sub">
            Every claim on this site maps to a committed artifact: a frozen prompt with a
            sha256, a run record with weights revisions and timings, or a reviewed submission.
            Nothing is inferred from how an image looks.
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 24 }}>
        <div className="container detail-grid">
          <div>
            <div className="prompt-block">
              <div className="head">
                <b>How a case is built</b>
              </div>
              <div style={{ padding: '14px 16px', fontSize: 14.5, color: 'var(--text-dim)' }}>
                <ol style={{ paddingLeft: 20, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <li>
                    <b style={{ color: 'var(--text)' }}>Prompt freeze.</b> A prompt from the
                    MIT-licensed awesome-gpt-image-2 library is copied verbatim (one recorded
                    template-variable fill for case-390), hashed, and becomes immutable. Cases
                    are independent — one prompt can be swapped without touching others.
                  </li>
                  <li>
                    <b style={{ color: 'var(--text)' }}>Qwen run.</b> One local generation on RX
                    7900 XTX (native Windows ROCm), Quality profile: bf16 weights, 40 steps,
                    cfg 1.0, euler/simple, fixed seed, canvas ≤ ~1.05 MP. Weights
                    (Comfy-Org/Qwen-Image-2.1 @ <span className="mono">aacf31a</span>) and
                    ComfyUI (<span className="mono">b5a4321</span>) are pinned by commit; the
                    engine repo (<span className="mono">qwen-image-rocm</span>) is pinned by
                    commit too. Failures are published as failures.
                  </li>
                  <li>
                    <b style={{ color: 'var(--text)' }}>Open challenge.</b> The GPT side starts
                    empty and is labeled <span className="badge open"><span className="dot" />Open Challenge</span>{' '}
                    until a submission arrives.
                  </li>
                  <li>
                    <b style={{ color: 'var(--text)' }}>Community submission.</b> A contributor
                    runs the BYOK CLI (or their own interface), submits image + run evidence
                    via issue/PR. Status becomes{' '}
                    <span className="badge community"><span className="dot" />Community Submitted</span>.
                  </li>
                  <li>
                    <b style={{ color: 'var(--text)' }}>Review.</b> A maintainer verifies the
                    evidence package (model snapshot, size/quality, prompt sha, usage record,
                    rights declaration). Accepted submissions make the case a{' '}
                    <span className="badge reviewed"><span className="dot" />Reviewed Comparison</span>;
                    rejected ones are archived with the reason.
                  </li>
                </ol>
              </div>
            </div>

            <div className="callout" style={{ marginTop: 16 }}>
              <b>Why the GPT side can be pixel-matched.</b> gpt-image-2 accepts custom sizes
              (16-px multiples, 0.66–8.3 MP, ratio ≤ 3:1). Each case's default GPT size equals
              the exact Qwen canvas — e.g. 720×1280 — so both models render the same aspect and
              pixel budget. Contributors can override; overrides are recorded in the run record.
            </div>
          </div>

          <aside>
            <div className="prompt-block" style={{ marginBottom: 16 }}>
              <div className="head">
                <b>Verification rules</b>
              </div>
              <div style={{ padding: '12px 16px', fontSize: 13.5, color: 'var(--text-dim)' }}>
                <ul style={{ paddingLeft: 18, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <li>Model identity is never inferred from visual similarity.</li>
                  <li>Automated validation re-computes every prompt and image sha256 on build.</li>
                  <li>Failed Qwen runs are never replaced by other images; cases without a run stay visibly failed.</li>
                  <li>No rankings, vote counts, or star numbers exist anywhere on this site unless they are real and sourced.</li>
                  <li>Every case page links its library source and original author label.</li>
                </ul>
              </div>
            </div>
            <div className="prompt-block">
              <div className="head">
                <b>Current totals</b>
              </div>
              <div style={{ padding: '12px 16px' }}>
                <table className="meta-table">
                  <tbody>
                    <tr><th>Frozen cases</th><td>{siteModel.totals.cases}</td></tr>
                    <tr><th>Qwen generations</th><td>{siteModel.totals.qwen_generated}</td></tr>
                    <tr><th>Open challenges</th><td>{siteModel.totals.open_challenges}</td></tr>
                    <tr><th>Community submitted</th><td>{siteModel.totals.community_submitted}</td></tr>
                    <tr><th>Reviewed comparisons</th><td>{siteModel.totals.reviewed_comparisons}</td></tr>
                    <tr><th>Blocked</th><td>{siteModel.totals.blocked}</td></tr>
                  </tbody>
                </table>
                <p className="muted small" style={{ marginBottom: 0 }}>
                  Full documents:{' '}
                  <a href={`${repoUrl}/blob/main/docs/METHODOLOGY.md`}>METHODOLOGY.md</a>,{' '}
                  <a href={`${repoUrl}/blob/main/docs/P0_AUDIT.md`}>P0_AUDIT.md</a>,{' '}
                  <a href={`${repoUrl}/blob/main/docs/QWEN_12_CASE_RESULTS.md`}>QWEN_12_CASE_RESULTS.md</a>.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
