import { siteModel, repoUrl } from '../components/Layout';

export default function Contribute() {
  const exampleCase = siteModel.cases.find((c) => c.status === 'OPEN_CHALLENGE') ?? siteModel.cases[0];

  return (
    <main>
      <section className="hero" style={{ paddingBottom: 10 }}>
        <div className="container">
          <span className="kicker">
            <span className="dot" />
            Bring Your Own Key — your key never leaves your machine
          </span>
          <h1>
            Submit your <span className="side-a">GPT Image 2</span> result
          </h1>
          <p className="sub">
            This project has no OpenAI API key by design. You run the generation locally with
            your own key, keep every cent of control (an explicit cost confirmation happens
            before any paid request), and attach the outputs to a GitHub issue or PR. Reviewed
            submissions become the GPT side of a challenge — with your attribution.
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 24 }}>
        <div className="container">
          <div className="paths-grid">
            <div className="path-card">
              <div className="step">Path 1 · CLI</div>
              <h3>Generate with your key</h3>
              <p>
                One command reads the frozen prompt, shows model, size, quality and estimated
                cost, and waits for your explicit confirmation. Exactly one image by default.
                Retries are bounded; your key is read from the environment and never written
                anywhere.
              </p>
              <pre>
{`# 1) your key, in the environment only
$env:OPENAI_API_KEY = "sk-..."   # PowerShell
#    export OPENAI_API_KEY=sk-...  # bash

# 2) preview cost -> confirm -> generate
uv run --no-project python -I \\
   tools/generate_gpt.py --case ${exampleCase?.case_id ?? 'case-443'}

# outputs: image.png + run.json + SUBMISSION.md`}
              </pre>
              <p className="muted small">
                Sizes are pixel- and aspect-matched to the Qwen canvas (gpt-image-2 accepts
                custom 16-px-multiple sizes), so both models face the same canvas.
              </p>
            </div>

            <div className="path-card">
              <div className="step">Path 2 · Issue</div>
              <h3>Submit via GitHub</h3>
              <p>
                Open a contribution issue, attach your image and the generated{' '}
                <code>SUBMISSION.md</code> (or fill the template by hand). Manual uploads are
                welcome too — they are labeled by evidence tier, not treated as verified.
              </p>
              <pre>
{`# pick a template:
${repoUrl}/issues/new?template=gpt_submission.md
${repoUrl}/issues/new?template=prompt_suggestion.md`}
              </pre>
              <p className="muted small">
                A PR adding files under <code>submissions/&lt;case&gt;/…</code> works the same
                way and is easier for maintainers to review.
              </p>
            </div>

            <div className="path-card">
              <div className="step">Path 3 · Review</div>
              <h3>Become a verified comparison</h3>
              <p>
                A maintainer checks the run evidence (model snapshot, size, usage record, prompt
                sha) against the public standard. Visual similarity is never accepted as proof
                of model identity.
              </p>
              <table className="tier-table">
                <thead>
                  <tr>
                    <th>Evidence</th>
                    <th>Tier shown on site</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>CLI run record with API usage</td>
                    <td>API-evidenced</td>
                  </tr>
                  <tr>
                    <td>Self-reported, other interface</td>
                    <td>Self-reported</td>
                  </tr>
                  <tr>
                    <td>Image only, no provenance</td>
                    <td>Not accepted</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="callout" style={{ marginTop: 22 }}>
            <b>Safety rules this project commits to.</b> No key ever enters a git file, an issue,
            a log, a screenshot, or this website — the site is fully static and never asks for
            credentials. The CLI reads <code>OPENAI_API_KEY</code> from your environment at
            runtime, self-scans every artifact it writes for key material, and never sends
            anything anywhere except <code>api.openai.com</code>. See{' '}
            <a href={`${repoUrl}/blob/main/docs/SECURITY.md`}>docs/SECURITY.md</a>.
          </div>
        </div>
      </section>
    </main>
  );
}
