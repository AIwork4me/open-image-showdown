export type CaseStatus =
  | 'OPEN_CHALLENGE'
  | 'COMMUNITY_SUBMITTED'
  | 'REVIEWED_COMPARISON'
  | 'BLOCKED';

export interface Reference {
  library: string;
  library_url: string;
  library_case_id: number;
  library_case_url: string | null;
  library_license: string;
  source_label: string | null;
  source_url: string | null;
  source_note: string;
}

export interface QwenGeneration {
  model: string;
  weights_repo: string;
  weights_revision: string;
  comfyui_commit: string;
  engine_repo: string;
  engine_commit: string;
  gpu: string;
  precision: string;
  steps: number;
  cfg: number;
  sampler: string;
  seed: number;
  size: string;
  wall_time_s: number;
  vram_peak_mb: number | null;
  generated_utc: string;
  non_square_probe: boolean;
}

export interface QwenSide {
  image: string;
  image_sha256: string;
  width: number;
  height: number;
  generation: QwenGeneration;
  license: string;
}

export interface SubmissionEvidence {
  model: string | null;
  model_snapshot: string | null;
  api_evidenced: boolean;
  run_record_available: boolean;
  method: string;
}

export interface Submission {
  id: string;
  state: 'pending' | 'accepted' | 'rejected';
  image: string;
  image_sha256: string;
  submitted_by: string;
  submitted_at: string | null;
  evidence: SubmissionEvidence;
  license_note: string;
}

export interface Case {
  case_id: string;
  status: CaseStatus;
  blocked_reason: string | null;
  title: { en: string; zh: string; library_title_zh: string };
  category: string;
  aspect: string;
  canvas: { width: number; height: number };
  prompt: string;
  prompt_sha256: string;
  prompt_language: string;
  prompt_derivation: {
    type: string;
    variable: string;
    value: string;
    upstream_prompt_sha256: string;
    description: string;
  } | null;
  reference: Reference;
  notes: string[];
  qwen: QwenSide | null;
  gpt: {
    planned_size: string;
    planned_quality: string;
    model: string;
    byok: boolean;
    submissions: number;
  };
  submissions: Submission[];
}

export interface SiteModel {
  schema_version: number;
  built_at: string;
  project: string;
  tagline: string;
  totals: {
    cases: number;
    qwen_generated: number;
    open_challenges: number;
    community_submitted: number;
    reviewed_comparisons: number;
    blocked: number;
  };
  cases: Case[];
}
