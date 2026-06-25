// Profile + lever metadata shared across the UI. The canonical source is the
// Rust `list_profiles` command; this mirror lets the app also render in a plain
// browser (dev preview) where Tauri's invoke() is unavailable.

export interface ProfileInfo {
  name: string;
  label: string;
  group: string;
  prior_precision_cap: number | null;
  precision_flexibility: number;
  discount_factor: number;
  rpe_noise_std: number;
  forward_model_update_rate: number;
  injury_noise_std: number;
  active_levers: string[];
}

export type LeverKey =
  | "prior_precision_cap"
  | "precision_flexibility"
  | "discount_factor"
  | "rpe_noise_std"
  | "forward_model_update_rate"
  | "injury_noise_std";

export interface LeverMeta {
  key: LeverKey;
  label: string;
  blurb: string;
  min: number;
  max: number;
  step: number;
  /** prior_precision_cap is nullable (None = unconstrained); we model None as max. */
  nullable?: boolean;
}

export const LEVERS: LeverMeta[] = [
  { key: "prior_precision_cap", label: "Prior precision cap", blurb: "Autism — weak priors. Lower = raw sensory data dominates.", min: 0.05, max: 3, step: 0.05, nullable: true },
  { key: "precision_flexibility", label: "Precision flexibility", blurb: "Autism (HIPPEA). Low = can't adapt learning rate to surprise.", min: 0.02, max: 1.5, step: 0.01 },
  { key: "discount_factor", label: "Discount factor γ", blurb: "ADHD. Lower = steeper devaluation of delayed reward.", min: 0.5, max: 0.99, step: 0.01 },
  { key: "rpe_noise_std", label: "Reward-gain noise", blurb: "ADHD. Higher = unstable, erratic reward learning.", min: 0, max: 1, step: 0.02 },
  { key: "forward_model_update_rate", label: "Forward-model update", blurb: "PPCS. Lower = sensorimotor mismatch persists.", min: 0.05, max: 1, step: 0.01 },
  { key: "injury_noise_std", label: "Injury noise", blurb: "PPCS. Higher = noisier vestibular afferent signal.", min: 0, max: 0.6, step: 0.02 },
];

// (color, group) per profile — Okabe-Ito, colorblind-safe (spec 9).
export const PROFILE_COLOR: Record<string, string> = {
  baseline: "#c7ccd9",
  autism_weak_prior: "#0072B2",
  autism_overfitting: "#56B4E9",
  adhd_discounting: "#D55E00",
  adhd_rpe_noise: "#E69F00",
  ppcs_forward_model: "#009E73",
  comorbid: "#CC79A7",
  audhd_emotion_dysregulation: "#b486ff",
};

export const BASELINE: ProfileInfo = {
  name: "baseline", label: "Baseline", group: "Reference",
  prior_precision_cap: null, precision_flexibility: 1, discount_factor: 0.95,
  rpe_noise_std: 0, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: [],
};

export const FALLBACK_PROFILES: ProfileInfo[] = [
  BASELINE,
  { name: "autism_weak_prior", label: "Autism — weak prior", group: "Autism", prior_precision_cap: 0.3, precision_flexibility: 1, discount_factor: 0.95, rpe_noise_std: 0, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: ["prior_precision_cap"] },
  { name: "autism_overfitting", label: "Autism — HIPPEA", group: "Autism", prior_precision_cap: null, precision_flexibility: 0.1, discount_factor: 0.95, rpe_noise_std: 0, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: ["precision_flexibility"] },
  { name: "adhd_discounting", label: "ADHD — discounting", group: "ADHD", prior_precision_cap: null, precision_flexibility: 1, discount_factor: 0.6, rpe_noise_std: 0, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: ["discount_factor"] },
  { name: "adhd_rpe_noise", label: "ADHD — unstable gain", group: "ADHD", prior_precision_cap: null, precision_flexibility: 1, discount_factor: 0.95, rpe_noise_std: 0.4, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: ["rpe_noise_std"] },
  { name: "ppcs_forward_model", label: "PPCS — forward model", group: "PPCS", prior_precision_cap: null, precision_flexibility: 1, discount_factor: 0.95, rpe_noise_std: 0, forward_model_update_rate: 0.3, injury_noise_std: 0.2, active_levers: ["forward_model_update_rate", "injury_noise_std"] },
  { name: "comorbid", label: "Comorbid (all levers)", group: "Comorbid", prior_precision_cap: 0.3, precision_flexibility: 0.1, discount_factor: 0.6, rpe_noise_std: 0.4, forward_model_update_rate: 0.3, injury_noise_std: 0.2, active_levers: ["prior_precision_cap", "precision_flexibility", "discount_factor", "rpe_noise_std", "forward_model_update_rate", "injury_noise_std"] },
  { name: "audhd_emotion_dysregulation", label: "AuDHD — emotion dysregulation", group: "Comorbid", prior_precision_cap: null, precision_flexibility: 0.15, discount_factor: 0.95, rpe_noise_std: 0.5, forward_model_update_rate: 1, injury_noise_std: 0, active_levers: ["precision_flexibility", "rpe_noise_std"] },
];
