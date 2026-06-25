import { useEffect, useMemo, useRef, useState } from "react";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TaskChart } from "@/components/TaskChart";
import {
  makeDebouncedRunner, runVolatility, type ProfileInfo,
} from "@/lib/tauri-bridge";

interface Props {
  profile: ProfileInfo;
  onError: (msg: string) => void;
}

// Live parameter sliders (spec 11.2) — the highest-impact feature in the GUI.
// Drag precision_flexibility and watch the volatility-learning belief curve update
// in real time. Calls into Rust are debounced + request-ID guarded via
// makeDebouncedRunner so dragging feels responsive, not broken.
export function ParameterPanel({ profile, onError }: Props) {
  const [flex, setFlex] = useState(profile.precision_flexibility);
  const [curve, setCurve] = useState<number[]>([]);

  // Reset slider when the selected profile changes.
  useEffect(() => setFlex(profile.precision_flexibility), [profile]);

  const runner = useMemo(
    () => makeDebouncedRunner<number[]>(runVolatility, setCurve, onError, 200),
    [onError]
  );

  // Fire on every (debounced) slider change and once on mount/profile change.
  const firstRun = useRef(true);
  useEffect(() => {
    runner(flex);
    firstRun.current = false;
  }, [flex, runner]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Live lever — precision_flexibility (HGF volatility)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-4">
            <Slider
              value={[flex]}
              min={0.02}
              max={1.5}
              step={0.01}
              onValueChange={(v) => setFlex(v[0])}
              className="flex-1"
            />
            <span className="w-16 text-right font-mono text-sm">{flex.toFixed(2)}</span>
          </div>
          <p className="text-xs text-slate-500">
            Low flexibility (HIPPEA / autism_overfitting) cannot raise its learning
            rate after the unsignalled switch at trial 50 — watch reconvergence slow.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Volatility-switching belief (live)</CardTitle>
        </CardHeader>
        <CardContent>
          <TaskChart data={curve} label="belief about arm-A reward prob." />
        </CardContent>
      </Card>
    </div>
  );
}
