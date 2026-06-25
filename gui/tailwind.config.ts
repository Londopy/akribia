import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        "panel-2": "var(--panel-2)",
        "panel-hover": "var(--panel-hover)",
        border: "var(--border)",
        ink: "var(--text)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        // Okabe-Ito profile palette (shared intent with viz/style.py, spec 9)
        okabe: {
          black: "#000000", orange: "#E69F00", sky: "#56B4E9", green: "#009E73",
          yellow: "#F0E442", blue: "#0072B2", vermillion: "#D55E00", purple: "#CC79A7",
        },
      },
      boxShadow: {
        card: "0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 30px rgba(0,0,0,0.35)",
        glow: "0 0 0 1px rgba(86,180,233,0.4), 0 0 24px rgba(86,180,233,0.25)",
      },
      borderRadius: { xl: "14px", "2xl": "18px" },
    },
  },
  plugins: [],
} satisfies Config;
