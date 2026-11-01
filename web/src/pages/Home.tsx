import { siteModel, repoUrl, asset } from '../components/Layout';
import CaseCard from '../components/CaseCard';

function pick<T>(arr: T[], n: number): T[] {
  return arr.slice(0, n);
}

export default function Home() {
  const t = siteModel.totals;
  const heroCases = pick(
    siteModel.cases.filter((c) => c.qwen && c.status !== 'BLOCKED'),
    3
  );

  return (
    <main>
      <section className="hero">
        <div className="container">
          <span className="kicker">
            <span className="dot" />
            Independent · Open evidence · {t.cases} frozen prompts
          </span>
          <h1>
            <span className="side-a">GPT Image 2</span> vs <span className="side-b">Qwen-Image 2.1</span>
          </h1>
          <p className="tagline">
            Same Prompt. Two Models. You Decide. <span className="zh">同一提示词，两个模型，你来评判。</span>
          </p>
          <p className="sub">
            Every challenge below was run for real: Qwen-Image 2.1 generated locally on an AMD
            RX 7900 XTX under ROCm, with seeds, weights revisions and run records in the open.
            The GPT Image 2 side is deliberately <b>empty</b> — this project has no OpenAI key.
            Bring yours, generate the GPT side on your machine, and turn open challenges into
            verified comparisons.
          </p>
          <div className="hero-actions">
            <a className="btn primary" href="#/contribute">
              Bring your OpenAI key →
            </a>
            <a className="btn ghost" href="#challenges">
              Browse the {t.cases} challenges
            </a>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <b>{t.qwen_generated}</b>
              <span>real Qwen generations</span>
            </div>
            <div className="stat">
              <b>{t.open_challenges}</b>
              <span>open challenges awaiting GPT</span>
            </div>
            <div className="stat">
              <b>{t.reviewed_comparisons}</b>
              <span>reviewed comparisons</span>
            </div>
            <div className="stat">
              <b>bf16 · 40 steps</b>
              <span>quality mainline, seeds recorded</span>
            </div>
          </div>

          {heroCases.length > 0 && (
            <div className="hero-strip">
              {heroCases.map((c) => (
                <a key={c.case_id} href={`#/case/${c.case_id}`}>
                  <img src={asset(c.qwen!.image)} alt={`${c.title.en} — Qwen-Image 2.1`} />
                  <span className="cap">
                    <b>{c.title.en}</b>
                    Qwen-Image 2.1 · {c.canvas.width}×{c.canvas.height} · seed {c.qwen!.generation.seed}
                  </span>
                </a>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="section" id="challenges">
        <div className="container">
          <div className="section-head">
            <h2>The Challenges</h2>
            <span className="count">
              {t.cases} frozen prompts · {t.open_challenges} open · {t.reviewed_comparisons} reviewed
            </span>
            <span className="spacer" />
            <a className="link" href="#/methodology">
              How verification works →
            </a>
          </div>
          <div className="case-grid">
            {siteModel.cases.map((c) => (
              <CaseCard key={c.case_id} c={c} />
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="callout">
            <b>No fake pairs, ever.</b> A GPT image only appears on a case page after a
            contributor submits it with run evidence and a maintainer reviews it against the{' '}
            <a href="#/methodology">public standard</a>. Until then you see exactly what exists:
            one real Qwen output and an honest empty slot. Prompt texts come from the MIT-licensed{' '}
            <a href="https://github.com/freestylefly/awesome-gpt-image-2">awesome-gpt-image-2</a>{' '}
            library with per-case attribution. Full audit trail:{' '}
            <a href={`${repoUrl}/blob/main/docs/P0_AUDIT.md`}>docs/P0_AUDIT.md</a>.
          </div>
        </div>
      </section>
    </main>
  );
}
