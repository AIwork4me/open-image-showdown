import type { Case } from '../types';
import { asset } from './Layout';

/**
 * The reference side of a comparison — a Community Gallery Reference image
 * from the awesome-gpt-image-2 library.
 *
 * Two honest states, nothing in between:
 *  - renderable (rights APPROVED + mirrored + sha-verified): the real image,
 *    always labeled "Community Gallery Reference — Model Unverified";
 *  - otherwise: a clearly-marked link-out card. NEVER a placeholder image
 *    pretending to be the reference, never a hotlink.
 */
export default function ReferencePanel({
  c,
  onZoom,
  compact,
}: {
  c: Case;
  onZoom?: (src: string, cap: string) => void;
  compact?: boolean;
}) {
  const ri = c.reference_image;
  if (!ri) {
    return (
      <div className="panel side-ref">
        <div className="panel-head">
          Reference
          <span className="sub">no reference record</span>
        </div>
        <div className="pending-slot">
          <p className="big">This case has no library reference image.</p>
        </div>
      </div>
    );
  }

  const statusText =
    ri.display_permission === 'APPROVED'
      ? 'displayed with author permission'
      : ri.display_permission === 'EXTERNAL_LINK_ONLY'
        ? 'external link only — not mirrored'
        : ri.display_permission === 'BLOCKED'
          ? 'blocked by rights holder'
          : 'author permission pending';

  if (!ri.renderable) {
    return (
      <div className="panel side-ref">
        <div className="panel-head">
          Community Gallery Reference
          <span className="sub">model unverified</span>
        </div>
        <div className="ref-linkout">
          <span className="badge neutral">
            <span className="dot" />
            Model Unverified
          </span>
          <span className="badge open">
            <span className="dot" />
            {statusText}
          </span>
          <p className="big">
            The reference image lives at the prompt library — we mirror it here
            only after its author approves ({ri.width}×{ri.height}{' '}
            {ri.original_author}).
          </p>
          <div className="ref-actions">
            <a className="btn primary" href={ri.library_case_url} target="_blank" rel="noreferrer">
              View reference at the library ↗
            </a>
            {ri.original_post_url && (
              <a className="btn ghost" href={ri.original_post_url} target="_blank" rel="noreferrer">
                Original post by {ri.original_author} ↗
              </a>
            )}
          </div>
          <p className="ref-why">
            Why not show it directly? The library's images belong to their original authors and
            carry no redistribution license — see{' '}
            <a href="https://github.com/AIwork4me/open-image-showdown/blob/main/docs/REFERENCE_IMAGE_AUDIT.md">
              the rights audit
            </a>
            . Authors can approve in one reply.
          </p>
        </div>
        {!compact && (
          <div className="panel-foot">
            <span className="chip">{ri.prompt_match_level === 'EXACT' ? 'exact prompt' : 'derived prompt'}</span>
            <span className="chip">ref {ri.width}×{ri.height}</span>
            <span className="chip">{ri.original_author}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="panel side-ref">
      <div className="panel-head">
        Community Gallery Reference
        <span className="sub">model unverified · {statusText}</span>
      </div>
      <div className="img-holder">
        <img
          src={asset(ri.image!)}
          alt={`${c.title.en} — community gallery reference (model unverified)`}
          onClick={() => onZoom?.(asset(ri.image!), `${c.title.en} — Community Gallery Reference (unverified)`)}
        />
      </div>
      <div className="panel-foot">
        <span className="chip">{ri.prompt_match_level === 'EXACT' ? 'exact prompt' : 'derived prompt'}</span>
        <span className="chip">{ri.width}×{ri.height}</span>
        <span className="chip">{ri.original_author}</span>
        <span className="chip mono" title={ri.image_sha256}>
          sha {ri.image_sha256.slice(0, 10)}…
        </span>
        <span className="chip link-chip">
          <a href={asset(ri.image!)} target="_blank" rel="noreferrer">
            full size ↗
          </a>
        </span>
        {ri.original_post_url && (
          <span className="chip link-chip">
            <a href={ri.original_post_url} target="_blank" rel="noreferrer">
              original post ↗
            </a>
          </span>
        )}
      </div>
    </div>
  );
}
