import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Thesis + required framing (spec 5). The GUI states the disclaimer too.
export function About() {
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Card className="animate-rise">
        <CardHeader><CardTitle>One inference engine. Three miscalibrations. Same math.</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed text-muted">
          <p>
            Predictive coding treats the brain as a hierarchical inference machine: a
            <span className="text-ink"> prediction</span> meets <span className="text-ink">evidence</span>,
            the mismatch is a <span className="text-ink">prediction error</span>, and that error is weighted
            by <span className="text-ink">precision</span> before updating beliefs. The same precision-weighting
            math, miscalibrated at different points, reproduces autism, ADHD and PPCS — and a comorbid (AuDHD) case
            is just more than one miscalibration at once.
          </p>
          <p>
            Every chart in this app is computed by the <span className="text-ink">same Rust core</span> the
            research layer validates. Pick a profile, drag a lever, and watch the behaviour change against the
            neurotypical baseline.
          </p>
        </CardContent>
      </Card>

      <Card className="animate-rise border-okabe-vermillion/40" style={{ animationDelay: "60ms" }}>
        <CardHeader><CardTitle className="text-okabe-orange">Not a diagnostic tool</CardTitle></CardHeader>
        <CardContent className="text-sm leading-relaxed text-muted">
          akribia implements <span className="text-ink">published, contested</span> mathematical models to
          illustrate theoretical mechanisms. It is not a diagnostic tool, has not been validated against patient
          data, and should not be used to assess or characterize any individual's condition. It runs entirely on
          synthetic data and collects nothing. The autism precision-weighting literature in particular is actively
          contested — this models competing hypotheses, not settled fact.
        </CardContent>
      </Card>
    </div>
  );
}
