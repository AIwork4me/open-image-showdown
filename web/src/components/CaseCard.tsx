import type { Case } from '../types';
import StatusBadge from './StatusBadge';
import { asset } from './Layout';

/** Dual-thumb case card: left = community gallery reference (only when its
 *  rights record is APPROVED and mirrored — otherwise an explicit link-out
 *  chip, never a fake substitute image), right = the real Qwen output. */
export default function CaseCard({ c }: { c: Case }) {
  const ri = c.reference_image;
  return (
    <a className="case-card" href={`#/case/${c.case_id}`}>
      <div className="thumb dual">
        {ri?.renderable ? (
          <div className="ref-half">
            <img
              src={asset(ri.image!)}
              alt={`${c.title.en} — community gallery reference (model unverified)`}
              loading="lazy"
            />
            <span className="side-label ref">Reference · unverified</span>
          </div>
        ) : (
          <div className="ref-half pending">
            <span className="side-label ref">Reference</span>
            <span className="ref-pending-text">
              {ri
                ? ri.display_permission === 'PENDING_PERMISSION'
                  ? 'permission pending ↗'
                  : 'view at library ↗'
                : 'no reference'}
            </span>
          </div>
        )}
        <div className="qwen-half">
          {c.qwen ? (
            <img src={asset(c.qwen.image_web ?? c.qwen.image)} alt={`${c.title.en} — Qwen-Image 2.1 output`} loading="lazy" />
          ) : (
            <div className="pending">Qwen generation pending / failed — see case page</div>
          )}
          <span className="side-label qwen">Qwen-Image 2.1</span>
        </div>
        <span className="model-tag chip">{c.aspect}</span>
      </div>
      <div className="body">
        <div className="titles">
          <b>{c.title.en}</b>
          <span>{c.title.zh}</span>
        </div>
        <div className="meta">
          <span className="chip">{c.category}</span>
          <span className="chip">
            {c.canvas.width}×{c.canvas.height}
          </span>
          {ri && !ri.aspect_match && <span className="chip warn-chip">ref aspect differs</span>}
          {ri?.prompt_match_level === 'DERIVED_TEMPLATE_FILL' && (
            <span className="chip warn-chip">derived prompt</span>
          )}
          {c.variant_of && <span className="chip">variant of #{c.variant_of.replace('case-', '')}</span>}
        </div>
        <StatusBadge status={c.status} />
      </div>
    </a>
  );
}
