import * as React from "react";
import { Card, CardContent, CardDesc, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  title: string;
  desc: string;
  metric?: { label: string; value: string; color?: string };
  children: React.ReactNode;
  delay?: number;
}

// A single task panel: title, one-line explanation, a live metric chip, and a chart.
export function TaskCard({ title, desc, metric, children, delay = 0 }: Props) {
  return (
    <Card className="animate-rise overflow-hidden" style={{ animationDelay: `${delay}ms` }}>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDesc className="mt-1">{desc}</CardDesc>
          </div>
          {metric && (
            <div className="shrink-0 rounded-lg border border-border bg-panel-2 px-2.5 py-1 text-right">
              <div className="text-[9px] uppercase tracking-wider text-muted">{metric.label}</div>
              <div className="font-mono text-sm font-semibold" style={{ color: metric.color ?? "var(--accent)" }}>
                {metric.value}
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
