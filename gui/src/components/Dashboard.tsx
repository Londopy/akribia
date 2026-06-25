import { useEffect, useRef, useState } from "react";
import { BarPair, CurveOverlay, OverlayLine } from "@/components/charts";
import { TaskCard } from "@/components/TaskChart";
import { engine } from "@/lib/engine";
import { PROFILE_COLOR, type ProfileInfo } from "@/lib/profiles";
import type { Levers } from "@/components/ParameterPanel";

// Debounce an object value (spec 11.2: avoid firing a re-run on every pixel).
function useDebounced<T>(value: T, delay = 180): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return v;
}

const capOf = (levers: Levers) =>
  levers.prior_precision_cap >= 3 ? null : levers.prior_precision_cap;

interface Series {
  illusion: number;
  vol: number[];
  disc: [number, number][];
  motion: number[];
  pert: number[];
}

const EMPTY: Series = { illusion: 0, vol: [], disc: [], motion: [], pert: [] };

async function compute(levers: Levers): Promise<Series> {
  const [illusion, vol, disc, motion, pert] = await Promise.all([
    engine.illusion(capOf(levers)),
    engine.volatility(levers.precision_flexibility),
    engine.discounting(levers.discount_factor),
    engine.selfMotion(levers.forward_model_update_rate, levers.injury_noise_std),
    engine.perturbation(levers.precision_flexibility, levers.rpe_noise_std),
  ]);
  return { illusion, vol, disc, motion, pert };
}

const BASE_LEVERS: Levers = {
  prior_precision_cap: 3, precision_flexibility: 1, discount_factor: 0.95,
  rpe_noise_std: 0, forward_model_update_rate: 1, injury_noise_std: 0,
};

interface Props {
  profile: ProfileInfo;
  levers: Levers;
  onError: (m: string) => void;
}

export function Dashboard({ profile, levers, onError }: Props) {
  const color = PROFILE_COLOR[profile.name] ?? "var(--accent)";
  const debounced = useDebounced(levers);
  const [base, setBase] = useState<Series>(EMPTY);
  const [cur, setCur] = useState<Series>(EMPTY);
  const req = useRef(0);

  // Baseline computed once.
  useEffect(() => {
    compute(BASE_LEVERS).then(setBase).catch((e) => onError(String(e)));
  }, [onError]);

  // Current series recomputed on (debounced) lever change, stale-guarded.
  useEffect(() => {
    const id = ++req.current;
    compute(debounced)
      .then((s) => { if (id === req.current) setCur(s); })
      .catch((e) => { if (id === req.current) onError(String(e)); });
  }, [debounced, onError]);

  // ---- lightweight live metrics derived from the series ---- //
  const reconverge = (() => {
    const i = cur.vol.findIndex((v, idx) => idx >= 50 && v < 0.5);
    return i < 0 ? "—" : `${i - 50} trials`;
  })();
  const auc = cur.disc.length
    ? (cur.disc.reduce((a, [, y]) => a + y, 0) / cur.disc.length).toFixed(2)
    : "—";
  const residual = cur.motion.length
    ? (cur.motion.slice(-10).reduce((a, b) => a + b, 0) / 10).toFixed(2)
    : "—";
  const recovery = (() => {
    const post = cur.pert.slice(30);
    const i = post.findIndex((v) => v < 1);
    return i < 0 ? ">50" : `${i}`;
  })();

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <TaskCard
        title="Illusory contour (Kanizsa)"
        desc="Weak priors reduce susceptibility — the absent local evidence dominates."
        metric={{ label: "score", value: cur.illusion.toFixed(2), color }}
        delay={0}
      >
        <BarPair baseline={base.illusion} current={cur.illusion} currentColor={color} />
      </TaskCard>

      <TaskCard
        title="Volatility switch"
        desc="An unsignalled reward flip at trial 50. Inflexible precision reconverges slowly."
        metric={{ label: "reconverge", value: reconverge, color }}
        delay={60}
      >
        <OverlayLine baseline={base.vol} current={cur.vol} currentColor={color} markerX={50} yDomain={[-0.1, 1.1]} />
      </TaskCard>

      <TaskCard
        title="Delay discounting"
        desc="Subjective value of a delayed reward. Steeper γ collapses the curve."
        metric={{ label: "AUC", value: auc, color }}
        delay={120}
      >
        <CurveOverlay baseline={base.disc} current={cur.disc} currentColor={color} />
      </TaskCard>

      <TaskCard
        title="Vestibular mismatch (PPCS)"
        desc="Self-motion vs. predicted signal. Impaired forward model fails to habituate."
        metric={{ label: "residual", value: residual, color }}
        delay={180}
      >
        <OverlayLine baseline={base.motion} current={cur.motion} currentColor={color} />
      </TaskCard>

      <TaskCard
        title="Perturbation recovery (AuDHD)"
        desc="A salient event mid-run. Slow return = inertia; jitter = unstable gain."
        metric={{ label: "recovery", value: recovery, color }}
        delay={240}
      >
        <OverlayLine baseline={base.pert} current={cur.pert} currentColor={color} markerX={30} />
      </TaskCard>

      <TaskCard
        title="Active levers"
        desc="The parameters this profile perturbs, relative to baseline."
        delay={300}
      >
        <div className="flex min-h-[200px] flex-wrap content-start gap-2 pt-1">
          {profile.active_levers.length === 0 && (
            <span className="text-sm text-muted">Baseline — all levers at neutral.</span>
          )}
          {profile.active_levers.map((k) => (
            <span
              key={k}
              className="rounded-lg border px-2.5 py-1 text-xs"
              style={{ borderColor: `${color}66`, color: "var(--text)", background: `${color}14` }}
            >
              {k}
            </span>
          ))}
        </div>
      </TaskCard>
    </div>
  );
}
