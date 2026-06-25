// Unified engine API. In the packaged desktop app it calls the Rust core via
// Tauri `invoke()` (the validated math, spec 11.1). In a plain browser (dev
// preview, where Tauri is absent) it falls back to a compact TypeScript mirror
// of the same equations so the dashboard still renders live curves. The mirror
// is preview-only — the desktop binary always uses Rust.

import { FALLBACK_PROFILES, type ProfileInfo } from "./profiles";

const isTauri =
  typeof window !== "undefined" &&
  ("__TAURI_INTERNALS__" in window || "__TAURI__" in window);

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const mod = await import("@tauri-apps/api/core");
  return mod.invoke<T>(cmd, args);
}

// ---- JS mirror of the core math (preview fallback) ---------------------- //
const VAR_EPS = 1e-6;
const clampVar = (v: number) => (Number.isNaN(v) ? VAR_EPS : Math.max(v, VAR_EPS));

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function gauss(rand: () => number, std: number) {
  const u = Math.max(rand(), 1e-12), v = rand();
  return std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function jsIllusion(cap: number | null): number {
  // P(C) from inducers ~ 0.99; perceived = precision-weighted fuse of top-down + bottom-up.
  const pc = 0.99;
  const perceived = (topDown: number, bottomUp: number) => {
    let precPrior = 1 / clampVar(1.0);
    if (cap != null) precPrior = Math.min(precPrior, cap);
    const precLike = 1 / clampVar(1.0);
    const post = precPrior + precLike;
    return (precPrior * topDown + precLike * bottomUp) / post;
  };
  return perceived(pc, 0) - perceived(0, 0);
}

function jsVolatility(flex: number): number[] {
  const obs = [...Array(50).fill(1), ...Array(50).fill(0)];
  let mu1 = 0, var1 = 1, mu2 = 0;
  const precLike = 1 / clampVar(1.0);
  const out: number[] = [];
  for (const z of obs) {
    const q = 0.005 + flex * Math.max(mu2, 0);
    const predVar1 = clampVar(var1 + q);
    const precPrior = 1 / predVar1;
    const post = precPrior + precLike;
    const pe = z - mu1;
    const lr = precLike / post;
    out.push(mu1);
    mu1 = mu1 + lr * pe;
    var1 = 1 / post;
    mu2 = Math.max(0.5 * mu2 + 0.5 * (pe * pe * precLike), 0);
  }
  return out;
}

const jsDiscounting = (gamma: number): [number, number][] =>
  Array.from({ length: 46 }, (_, i) => [i * 2, Math.pow(gamma, i * 2)]);

function jsSelfMotion(updateRate: number, injury: number, seed: number): number[] {
  const cmd = [...Array(50).fill(30), ...Array(30).fill(0)];
  const rand = mulberry32(seed);
  let est = 0;
  return cmd.map((c) => {
    const predicted = est;
    let actual = c;
    if (injury > 0) actual += gauss(rand, injury);
    const mismatch = actual - predicted;
    est += updateRate * mismatch;
    return Math.abs(mismatch);
  });
}

function jsPerturbation(flex: number, rpe: number, seed: number): number[] {
  const n = 80, at = 30, mag = 10;
  const lr = 0.05 + 0.25 * Math.min(flex, 1);
  const rand = mulberry32(seed);
  const arousal: number[] = Array(at).fill(0);
  let v = mag;
  for (let i = 0; i < n - at; i++) {
    let pe = 0 - v;
    if (rpe > 0) pe += gauss(rand, rpe);
    v = v + lr * pe;
    arousal.push(Math.abs(v));
  }
  return arousal;
}

// ---- Public API --------------------------------------------------------- //
export const BACKEND: "rust" | "browser" = isTauri ? "rust" : "browser";

export const engine = {
  backend: BACKEND,
  async listProfiles(): Promise<ProfileInfo[]> {
    if (isTauri) return invoke<ProfileInfo[]>("list_profiles");
    return FALLBACK_PROFILES;
  },
  async illusion(cap: number | null): Promise<number> {
    return isTauri ? invoke<number>("run_illusion", { priorPrecisionCap: cap }) : jsIllusion(cap);
  },
  async volatility(flex: number): Promise<number[]> {
    return isTauri ? invoke<number[]>("run_volatility", { precisionFlexibility: flex }) : jsVolatility(flex);
  },
  async discounting(gamma: number): Promise<[number, number][]> {
    return isTauri ? invoke<[number, number][]>("run_discounting", { discountFactor: gamma }) : jsDiscounting(gamma);
  },
  async selfMotion(updateRate: number, injury: number, seed = 7): Promise<number[]> {
    return isTauri
      ? invoke<number[]>("run_self_motion", { updateRate, injuryNoiseStd: injury, seed })
      : jsSelfMotion(updateRate, injury, seed);
  },
  async perturbation(flex: number, rpe: number, seed = 7): Promise<number[]> {
    return isTauri
      ? invoke<number[]>("run_perturbation", { precisionFlexibility: flex, rpeNoiseStd: rpe, seed })
      : jsPerturbation(flex, rpe, seed);
  },
};

/** Debounce a value->result async call AND discard stale in-flight results via a
 *  request-ID guard (spec 11.2 — the difference between "responsive" and "broken"). */
export function makeDebouncedRunner<T>(
  fn: (value: number) => Promise<T>,
  onResult: (r: T) => void,
  onError: (m: string) => void,
  delayMs = 180,
) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let latest = 0;
  return (value: number) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(async () => {
      const id = ++latest;
      try {
        const r = await fn(value);
        if (id === latest) onResult(r);
      } catch (e) {
        if (id === latest) onError(String(e));
      }
    }, delayMs);
  };
}
