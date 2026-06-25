import { RotateCcw } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { LEVERS, PROFILE_COLOR, type ProfileInfo } from "@/lib/profiles";
import { cn } from "@/lib/utils";

export type Levers = Record<string, number>;

interface Props {
  profile: ProfileInfo;
  levers: Levers;
  onChange: (key: string, value: number) => void;
  onReset: () => void;
}

// Live parameter sliders (spec 11.2). Active levers for the selected profile are
// highlighted; dragging any of them updates the dashboard charts in real time.
export function ParameterPanel({ profile, levers, onChange, onReset }: Props) {
  const accent = PROFILE_COLOR[profile.name] ?? "var(--accent)";
  return (
    <div className="rounded-2xl border border-border bg-panel p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">Levers</div>
          <div className="text-xs text-muted">Drag to watch the model's behaviour change live.</div>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs text-muted transition hover:bg-panel-hover hover:text-ink"
        >
          <RotateCcw size={13} /> reset
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {LEVERS.map((l) => {
          const isActive = profile.active_levers.includes(l.key);
          const val = levers[l.key];
          const display =
            l.nullable && val >= l.max ? "∞ (off)" : val.toFixed(2);
          return (
            <div
              key={l.key}
              className={cn(
                "rounded-xl border p-3 transition",
                isActive ? "border-transparent bg-panel-2 shadow-card" : "border-border/60 bg-transparent opacity-70",
              )}
              style={isActive ? { boxShadow: `inset 0 0 0 1px ${accent}55` } : undefined}
            >
              <div className="mb-2 flex items-baseline justify-between gap-2">
                <span className="text-xs font-medium text-ink">{l.label}</span>
                <span className="font-mono text-xs text-muted">{display}</span>
              </div>
              <Slider
                value={[val]}
                min={l.min}
                max={l.max}
                step={l.step}
                accent={isActive ? accent : "#3a4560"}
                onValueChange={(v) => onChange(l.key, v[0])}
              />
              <p className="mt-2 text-[10.5px] leading-snug text-muted">{l.blurb}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
