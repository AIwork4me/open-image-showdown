import type { CaseStatus } from '../types';

const MAP: Record<CaseStatus, { cls: string; label: string; hint: string }> = {
  OPEN_CHALLENGE: {
    cls: 'open',
    label: 'Open Challenge',
    hint: 'Real Qwen output only — waiting for a GPT Image 2 submission',
  },
  COMMUNITY_SUBMITTED: {
    cls: 'community',
    label: 'Community Submitted',
    hint: 'A GPT result was submitted and is awaiting maintainer review',
  },
  REVIEWED_COMPARISON: {
    cls: 'reviewed',
    label: 'Reviewed Comparison',
    hint: 'Both sides verified per the public review standard',
  },
  BLOCKED: { cls: 'blocked', label: 'Blocked', hint: 'Technical, licensing, or rights issue' },
};

export default function StatusBadge({ status, showHint = false }: { status: CaseStatus; showHint?: boolean }) {
  const m = MAP[status];
  return (
    <span className={`badge ${m.cls}`} title={m.hint}>
      <span className="dot" />
      {showHint ? m.hint : m.label}
    </span>
  );
}
