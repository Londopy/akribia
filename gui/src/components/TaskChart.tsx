import {
  Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid,
} from "recharts";

interface Props {
  data: number[];
  label: string;
  color?: string;
}

// Interactive in-app chart (spec 11.2) — recharts, lighter and idiomatic with
// Tailwind. The comparison_grid.py dashboard reimagined as a live view.
export function TaskChart({ data, label, color = "#0072B2" }: Props) {
  const series = data.map((y, i) => ({ t: i, value: y }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line type="monotone" dataKey="value" name={label} stroke={color}
              dot={false} strokeWidth={2} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
