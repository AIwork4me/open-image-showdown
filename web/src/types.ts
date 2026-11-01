export type CaseStatus =
  | 'OPEN_CHALLENGE'
  | 'COMMUNITY_SUBMITTED'
  | 'REVIEWED_COMPARISON'
  | 'BLOCKED';

/** Rights status of a library reference image (mirrors the rights ledger).
 *  Only APPROVED (+ mirrored, sha-verified) references may be rendered. */
export type ReferencePermission =
  | 'APPROVED'
  | 'EXTERNAL_LINK_ONLY'
  | 'PENDING_PERMISSION'
  | 'BLOCKED';

/** How a case page presents its comparison. Derived, never hand-set:
 *  VERIFIED_GPT_COMPARISON  reviewed community GPT submission exists
 *  REFERENCE_RECREATION     rights-APPROVED library reference + real Qwen run
 *  QWEN_ONLY                real Qwen run; reference is a labeled link-out */
export type DisplayMode =
  | 'VERIFIED_GPT_COMPARISON'
  | 'REFERENCE_RECREATION'
  | 'QWEN_ONLY';

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

/** Library reference image record (from gallery/reference/index.json).
 *  A reference image is a COMMUNITY GALLERY REFERENCE — its generating model
 *  is unverified and it is NEVER labeled as a verified GPT Image 2 output. */
export interface ReferenceImage {
  display_permission: ReferencePermission;
  renderable: boolean;          // APPROVED + mirrored + file exists
  image: string | null;         // site asset path when renderable
  image_sha256: string;         // audited upstream fingerprint
  width: number;                // upstream reference dims (facts, always present)
  height: number;
  original_author: string;
  original_post_url: string | null;
  original_author_profile_url: string | null;
  library_case_url: string;     // pinned-commit link (never mutable main)
  source_commit_sha: string;
  model_identity: string;       // always contains UNVERIFIED
  prompt_match_level: 'EXACT' | 'DERIVED_TEMPLATE_FILL';
  prompt_match_note: string;
  aspect_match: boolean;        // reference aspect vs Qwen canvas within 2%
  aspect_disclosure_required: boolean;
  attribution: string;
  reuse_restrictions: string;
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
  image: string;             // original PNG (full resolution, provenance-pinned)
  image_web: string | null;  // committed webp derivative for inline display
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
  display_mode: DisplayMode;
  variant_of: string | null;    // set for reference-pairing variants (case-390t)
  variant_kind: string | null;
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
  reference_image: ReferenceImage | null;
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
    cases: number;                 // primary (non-variant) challenges
    variants: number;
    qwen_generated: number;        // all real Qwen outputs incl. variants
    open_challenges: number;
    community_submitted: number;
    reviewed_comparisons: number;
    blocked: number;
    references_total: number;      // audited reference records (12)
    references_approved: number;   // renderable side-by-side references
    reference_pairings_ready: number;
  };
  cases: Case[];
}
