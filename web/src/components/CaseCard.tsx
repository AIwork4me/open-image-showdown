import type { Case } from '../types';
import StatusBadge from './StatusBadge';

export default function CaseCard({ c }: { c: Case }) {
  return (
    <a className="case-card" href={`#/case/${c.case_id}`}>
      <div className="thumb">
        {c.qwen ? (
          <img src={c.qwen.image} alt={`${c.title.en} — Qwen-Image 2.1 output`} loading="lazy" />
        ) : (
          <div className="pending">Qwen generation pending / failed — see case page</div>
        )}
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
        </div>
        <StatusBadge status={c.status} />
      </div>
    </a>
  );
}
