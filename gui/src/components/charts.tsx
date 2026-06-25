import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const GRID = "#202840";
const AXIS = "#6b7488";

const tooltipStyle = {
  background: "#0e1320",
  border: "1px solid #2a3550",
  borderRadius: 10,
  fontSize: 12,
  color: "#e7eaf3",
};

interface OverlayProps {
  baseline: number[];
  current: number[];
  currentColor: string;
  xLabel?: string;
  yLabel?: string;
  markerX?: number;
  height?: number;
  yDomain?: [number, number];
}

// Two series overlaid: dashed gray baseline + solid colored profile (color is
// never the only cue — line style differs too, spec 9).
export function OverlayLine({
  baseline, current, currentColor, markerX, height = 200, yDomain,
}: OverlayProps) {
  const data = current.map((v, i) => ({ t: i, base: baseline[i] ?? null, cur: v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 6, right: 10, bottom: 2, left: -18 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
        <XAxis dataKey="t" tick={{ fontSize: 10, fill: AXIS }} stroke={GRID} />
        <YAxis tick={{ fontSize: 10, fill: AXIS }} stroke={GRID} domain={yDomain ?? ["auto", "auto"]} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: AXIS }} />
        {markerX != null && <ReferenceLine x={markerX} stroke="#46506b" strokeDasharray="3 3" />}
        <Line type="monotone" dataKey="base" name="baseline" stroke="#c7ccd9" strokeWidth={1.5}
              strokeDasharray="5 4" dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="cur" name="profile" stroke={currentColor} strokeWidth={2.4}
              dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Discounting curve overlay on a log-ish feel (kept linear 0..1 fraction).
export function CurveOverlay({
  baseline, current, currentColor, height = 200,
}: { baseline: [number, number][]; current: [number, number][]; currentColor: string; height?: number }) {
  const data = current.map(([x, y], i) => ({ x, base: baseline[i]?.[1] ?? null, cur: y }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 6, right: 10, bottom: 2, left: -18 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="2 4" />
        <XAxis dataKey="x" tick={{ fontSize: 10, fill: AXIS }} stroke={GRID} />
        <YAxis tick={{ fontSize: 10, fill: AXIS }} stroke={GRID} domain={[0, 1]} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: AXIS }} />
        <Line type="monotone" dataKey="base" stroke="#c7ccd9" strokeWidth={1.5}
              strokeDasharray="5 4" dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="cur" stroke={currentColor} strokeWidth={2.4}
              dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function BarPair({
  baseline, current, currentColor, height = 200,
}: { baseline: number; current: number; currentColor: string; height?: number }) {
  const data = [
    { name: "baseline", v: baseline, fill: "#c7ccd9" },
    { name: "profile", v: current, fill: currentColor },
  ];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 6, right: 10, bottom: 2, left: -18 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="2 4" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: AXIS }} stroke={GRID} />
        <YAxis tick={{ fontSize: 10, fill: AXIS }} stroke={GRID} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="v" radius={[6, 6, 0, 0]}>
          {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
