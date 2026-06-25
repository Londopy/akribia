import { Activity, Cpu } from "lucide-react";
import { PROFILE_COLOR, type ProfileInfo } from "@/lib/profiles";
import { cn } from "@/lib/utils";

interface Props {
  profiles: ProfileInfo[];
  selected: string;
  onSelect: (name: string) => void;
  backend: "rust" | "browser";
}

// Profile sidebar (spec 11.2) — grouped, colored dots, active highlight.
export function ProfileSelector({ profiles, selected, onSelect, backend }: Props) {
  const groups = profiles.reduce<Record<string, ProfileInfo[]>>((acc, p) => {
    (acc[p.group] ||= []).push(p);
    return acc;
  }, {});

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-border bg-[#0d111b]/80">
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent/15 text-accent shadow-glow">
          <Activity size={18} />
        </div>
        <div>
          <div className="text-[15px] font-semibold leading-none">akribia</div>
          <div className="mt-1 text-[10px] uppercase tracking-widest text-muted">precision engine</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3">
        {Object.entries(groups).map(([group, items]) => (
          <div key={group} className="mb-4">
            <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-muted/70">
              {group}
            </div>
            <ul className="space-y-1">
              {items.map((p) => {
                const active = selected === p.name;
                return (
                  <li key={p.name}>
                    <button
                      onClick={() => onSelect(p.name)}
                      className={cn(
                        "group flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] transition",
                        active ? "bg-panel-hover text-ink shadow-card" : "text-muted hover:bg-panel hover:text-ink",
                      )}
                    >
                      <span
                        className={cn("h-2.5 w-2.5 shrink-0 rounded-full transition", active && "live-dot")}
                        style={{ background: PROFILE_COLOR[p.name] ?? "#888", boxShadow: active ? `0 0 10px ${PROFILE_COLOR[p.name]}` : "none" }}
                      />
                      <span className="truncate">{p.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-2 border-t border-border px-5 py-3 text-[11px] text-muted">
        <Cpu size={13} className={backend === "rust" ? "text-okabe-green" : "text-okabe-orange"} />
        engine:&nbsp;<span className="text-ink">{backend === "rust" ? "Rust core" : "browser preview"}</span>
      </div>
    </aside>
  );
}
