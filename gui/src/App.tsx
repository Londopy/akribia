import { useEffect, useState } from "react";
import { ProfileSelector } from "@/components/ProfileSelector";
import { ParameterPanel } from "@/components/ParameterPanel";
import { listProfiles, type ProfileInfo } from "@/lib/tauri-bridge";

export default function App() {
  const [profiles, setProfiles] = useState<ProfileInfo[]>([]);
  const [selected, setSelected] = useState("baseline");
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    listProfiles().then((p) => setProfiles(p)).catch((e) => setToast(String(e)));
  }, []);

  // Structured errors surfaced as a toast (spec 2.13), not a silent failure.
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(id);
  }, [toast]);

  const current = profiles.find((p) => p.name === selected);

  return (
    <div className="flex h-screen w-screen bg-white text-slate-900">
      <ProfileSelector profiles={profiles} selected={selected} onSelect={setSelected} />
      <main className="flex-1 overflow-y-auto p-6">
        <header className="mb-4">
          <h1 className="text-xl font-bold">akribia</h1>
          <p className="text-sm text-slate-500">
            One inference engine. Three miscalibrations. Same math. — calling the
            Rust core directly via Tauri.
          </p>
        </header>
        {current ? (
          <ParameterPanel profile={current} onError={setToast} />
        ) : (
          <p className="text-slate-400">Loading profiles…</p>
        )}
      </main>

      {toast && (
        <div className="fixed bottom-4 right-4 rounded-lg bg-okabe-vermillion px-4 py-3 text-sm text-white shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}
