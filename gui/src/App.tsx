import { useCallback, useEffect, useMemo, useState } from "react";
import { LayoutGrid, Info } from "lucide-react";
import { ProfileSelector } from "@/components/ProfileSelector";
import { ParameterPanel, type Levers } from "@/components/ParameterPanel";
import { Dashboard } from "@/components/Dashboard";
import { About } from "@/components/About";
import { engine } from "@/lib/engine";
import { FALLBACK_PROFILES, PROFILE_COLOR, type ProfileInfo } from "@/lib/profiles";
import { cn } from "@/lib/utils";

function leversFromProfile(p: ProfileInfo): Levers {
  return {
    // None (unconstrained) prior precision is modelled as the slider max (= "off").
    prior_precision_cap: p.prior_precision_cap ?? 3,
    precision_flexibility: p.precision_flexibility,
    discount_factor: p.discount_factor,
    rpe_noise_std: p.rpe_noise_std,
    forward_model_update_rate: p.forward_model_update_rate,
    injury_noise_std: p.injury_noise_std,
  };
}

type Tab = "explore" | "about";

export default function App() {
  const [profiles, setProfiles] = useState<ProfileInfo[]>(FALLBACK_PROFILES);
  const [selected, setSelected] = useState("autism_weak_prior");
  const [levers, setLevers] = useState<Levers>(() => leversFromProfile(FALLBACK_PROFILES[1]));
  const [tab, setTab] = useState<Tab>("explore");
  const [toast, setToast] = useState<string | null>(null);

  const profile = useMemo(
    () => profiles.find((p) => p.name === selected) ?? profiles[0],
    [profiles, selected],
  );

  useEffect(() => {
    engine.listProfiles().then(setProfiles).catch((e) => setToast(String(e)));
  }, []);

  const selectProfile = useCallback((name: string) => {
    setSelected(name);
    const p = (profiles.find((x) => x.name === name)) ?? FALLBACK_PROFILES[0];
    setLevers(leversFromProfile(p));
  }, [profiles]);

  const setLever = useCallback((key: string, value: number) => {
    setLevers((prev) => ({ ...prev, [key]: value }));
  }, []);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(id);
  }, [toast]);

  const color = PROFILE_COLOR[profile.name] ?? "var(--accent)";

  return (
    <div className="flex h-screen w-screen overflow-hidden text-ink">
      <ProfileSelector profiles={profiles} selected={selected} onSelect={selectProfile} backend={engine.backend} />

      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between border-b border-border px-6 py-3.5">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full live-dot" style={{ background: color, boxShadow: `0 0 12px ${color}` }} />
            <div>
              <h1 className="text-[15px] font-semibold leading-none">{profile.label}</h1>
              <p className="mt-1 text-xs text-muted">interactive precision-profile explorer</p>
            </div>
          </div>
          <nav className="flex items-center gap-1 rounded-xl border border-border bg-panel p-1">
            {([["explore", "Explore", LayoutGrid], ["about", "About", Info]] as const).map(([id, label, Icon]) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition",
                  tab === id ? "bg-panel-hover text-ink shadow-card" : "text-muted hover:text-ink",
                )}
              >
                <Icon size={14} /> {label}
              </button>
            ))}
          </nav>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {tab === "explore" ? (
            <div className="space-y-5">
              <ParameterPanel
                profile={profile}
                levers={levers}
                onChange={setLever}
                onReset={() => setLevers(leversFromProfile(profile))}
              />
              <Dashboard profile={profile} levers={levers} onError={setToast} />
            </div>
          ) : (
            <About />
          )}
        </div>
      </main>

      {toast && (
        <div className="fixed bottom-5 right-5 max-w-sm rounded-xl border border-okabe-vermillion/50 bg-[#1a1014] px-4 py-3 text-sm text-ink shadow-card">
          {toast}
        </div>
      )}
    </div>
  );
}
