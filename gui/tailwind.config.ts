import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Okabe-Ito colorblind-safe palette (spec 9), shared with viz/style.py.
        okabe: {
          black: "#000000", orange: "#E69F00", sky: "#56B4E9", green: "#009E73",
          yellow: "#F0E442", blue: "#0072B2", vermillion: "#D55E00", purple: "#CC79A7",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
