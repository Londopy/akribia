import type { ProfileInfo } from "@/lib/tauri-bridge";
import { cn } from "@/lib/utils";

interface Props {
  profiles: ProfileInfo[];
  selected: string;
  onSelect: (name: string) => void;
}

// Profile selector sidebar (spec 11.2) — switch between every profile in the
// catalog, including audhd_emotion_dysregulation.
export function ProfileSelector({ profiles, selected, onSelect }: Props) {
  return (
    <nav className="w-64 shrink-0 border-r border-slate-200 bg-slate-50 p-3 overflow-y-auto">
      <h2 className="px-2 pb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
        Profiles
      </h2>
      <ul className="space-y-1">
        {profiles.map((p) => (
          <li key={p.name}>
            <button
              onClick={() => onSelect(p.name)}
              className={cn(
                "w-full rounded-lg px-3 py-2 text-left text-sm transition",
                selected === p.name
                  ? "bg-okabe-blue text-white"
                  : "text-slate-700 hover:bg-slate-200"
              )}
            >
              {p.name}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
