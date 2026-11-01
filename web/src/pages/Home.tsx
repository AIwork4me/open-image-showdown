import { siteModel, repoUrl, asset } from '../components/Layout';
import CaseCard from '../components/CaseCard';
import ReferencePanel from '../components/ReferencePanel';

function pick<T>(arr: T[], n: number): T[] {
  return arr.slice(0, n);
}

/** The hero case: first rights-approved pairing if one exists, otherwise a
 *  curated visually-strong case (its reference renders as a link-out card
 *  until permissions arrive — never a fake image). */
function heroCase() {
  const primary = siteModel.cases.filter((c) => !c.variant_of && c.status !== 'BLOCKED');
  const paired = primary.find((c) => c.display_mode === 'REFERENCE_RECREATION' && c.qwen);
  return paired ?? primary.find((c) => c.case_id === 'case-443' && c.qwen) ?? primary.find((c) => c.qwen) ?? null;
}

export default function Home() {
  const t = siteModel.totals;
  const primaryCases = siteModel.cases.filter((c) => !c.variant_of);
  const variantCases = siteModel.cases.filter((c) => c.variant_of);
  const hero = heroCase();
  const heroStripCases = pick(
    primaryCases.filter((c) => c.qwen && c.status !== 'BLOCKED' && c.case_id !== hero?.case_id),
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
          <p className="hero-count">
            {t.references_approved > 0 ? (
              <>
                <b>{t.references_approved}</b> community gallery references × <b>{t.qwen_generated}</b> real Qwen
                reproductions
              </>
            ) : (
              <>
                <b>{t.qwen_generated}</b> real Qwen reproductions of <b>{t.references_total}</b> community prompts ·
                reference mirroring <b>{t.references_approved}/{t.references_total}</b> (author permissions pending)
              </>
            )}
          </p>

          {hero && hero.qwen && (
            <div className="hero-pair">
              <ReferencePanel c={hero} compact />
              <div className="panel side-qwen">
                <div className="panel-head">
                  Qwen-Image 2.1
                  <span className="sub">
                    bf16 · {hero.qwen.generation.steps} steps · seed {hero.qwen.generation.seed} · local ROCm run
                  </span>
                </div>
                <div className="img-holder">
                  <a href={`#/case/${hero.case_id}`}>
                    <img src={asset(hero.qwen.image_web ?? hero.qwen.image)} alt={`${hero.title.en} — Qwen-Image 2.1 output`} />
                  </a>
                </div>
                <div className="panel-foot">
                  <span className="chip">{hero.qwen.generation.size}</span>
                  <span className="chip">{hero.category}</span>
                  <a className="chip link-chip" href={`#/case/${hero.case_id}`}>
                    prompt · source · reproduce →
                  </a>
                </div>
              </div>
            </div>
          )}

          <div className="hero-actions">
            <a className="btn primary" href="#challenges">
              View the {t.cases} comparisons
            </a>
            <a className="btn ghost" href="#/contribute">
              Copy a prompt · Bring your key →
            </a>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <b>{t.qwen_generated}</b>
              <span>real Qwen generations</span>
            </div>
            <div className="stat">
              <b>
                {t.references_approved}/{t.references_total}
              </b>
              <span>references mirrored (rights-gated)</span>
            </div>
            <div className="stat">
              <b>{t.reviewed_comparisons}</b>
              <span>verified GPT comparisons</span>
            </div>
            <div className="stat">
              <b>bf16 · 40 steps</b>
              <span>quality mainline, seeds recorded</span>
            </div>
          </div>

          {heroStripCases.length > 0 && (
            <div className="hero-strip">
              {heroStripCases.map((c) => (
                <a key={c.case_id} href={`#/case/${c.case_id}`}>
                  <img src={asset(c.qwen!.image_web ?? c.qwen!.image)} alt={`${c.title.en} — Qwen-Image 2.1`} />
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
            <h2>The Comparisons</h2>
            <span className="count">
              {t.cases} frozen prompts · {t.open_challenges} open · {t.reviewed_comparisons} reviewed
            </span>
            <span className="spacer" />
            <a className="link" href="#/methodology">
              How verification works →
            </a>
          </div>
          <div className="case-grid">
            {primaryCases.map((c) => (
              <CaseCard key={c.case_id} c={c} />
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="callout">
            <b>Left side: community references, rights-gated. Right side: always real.</b> Every card's
            Qwen image is a genuine local run with its provenance committed. The community reference
            beside it appears as an image only after its original author approves — until then you get
            the honest link-out you see now. A reference is <b>never</b> labeled as a verified GPT
            Image 2 output; that label is reserved for reviewed submissions with run evidence.{' '}
            {variantCases.length > 0 && (
              <>
                Case #390 also ships an exact-prompt Turkey variant (
                {variantCases.map((v) => `#${v.case_id.replace('case-', '')}`).join(', ')}
                ){' '}
                for its Istanbul reference.{' '}
              </>
            )}
            Full audit trail:{' '}
            <a href={`${repoUrl}/blob/main/docs/REFERENCE_IMAGE_AUDIT.md`}>reference image audit</a> ·{' '}
            <a href={`${repoUrl}/blob/main/docs/PERMISSION_REQUEST_KIT.md`}>permission workflow</a>.
          </div>
        </div>
      </section>
    </main>
  );
}
