import { Outlet } from 'react-router-dom';
import site from '../data/cases.json';
import type { SiteModel } from '../types';

export const siteModel = site as unknown as SiteModel;
export const repoUrl = 'https://github.com/AIwork4me/open-image-showdown';

export default function Layout() {
  return (
    <>
      <header className="site-header">
        <div className="container inner">
          <a className="brand" href="#/">
            <span className="vs-chip">VS</span>
            Open Image Showdown
          </a>
          <nav className="nav">
            <a href="#/">Challenges</a>
            <a href="#/methodology">Methodology</a>
            <a href="#/contribute" className="cta">
              Bring your key →
            </a>
          </nav>
        </div>
      </header>
      <Outlet />
      <footer className="site-footer">
        <div className="container">
          <div className="cols">
            <div>
              <h4>Project</h4>
              <ul>
                <li><a href={`${repoUrl}#readme`}>GitHub repository</a></li>
                <li><a href="#/methodology">Methodology &amp; verification tiers</a></li>
                <li><a href={`${repoUrl}/blob/main/LICENSES_AND_SOURCES.md`}>Licenses &amp; sources</a></li>
                <li><a href={`${repoUrl}/blob/main/docs/P0_AUDIT.md`}>P0 audit</a></li>
              </ul>
            </div>
            <div>
              <h4>Participate</h4>
              <ul>
                <li><a href="#/contribute">Submit a GPT Image 2 result</a></li>
                <li><a href={`${repoUrl}/issues/new/choose`}>Open an issue</a></li>
                <li><a href={`${repoUrl}/blob/main/CONTRIBUTING.md`}>Contributing guide</a></li>
              </ul>
            </div>
            <div>
              <h4>Model provenance</h4>
              <ul>
                <li>Qwen side: local runs, RX 7900 XTX · ROCm</li>
                <li>Weights: Comfy-Org/Qwen-Image-2.1 @ <span className="mono">aacf31a</span></li>
                <li>GPT side: community BYOK · <span className="mono">gpt-image-2-2026-04-21</span></li>
              </ul>
            </div>
          </div>
          <p className="disclaimer">
            Independent community research project. Not affiliated with or endorsed by OpenAI,
            Alibaba/Qwen, or AMD. Qwen-side images are licensed CC BY-NC 4.0 (Qwen Research
            License governs the weights). GPT-side images belong to their contributors.
            Prompt texts republished under the MIT-licensed{' '}
            <a href={siteModel.cases[0]?.reference.library_url ?? '#'}>awesome-gpt-image-2</a>{' '}
            library with attribution. No model identity is ever assumed from visual similarity.
          </p>
        </div>
      </footer>
    </>
  );
}
