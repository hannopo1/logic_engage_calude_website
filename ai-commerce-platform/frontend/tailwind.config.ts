import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./context/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Premium "specialty coffee" system: warm ink + gold accent.
        // `brand` stays the gold CTA so existing bg-brand/text-brand keep working;
        // button backgrounds use brand-dark for AA contrast with white text.
        brand: {
          DEFAULT: "#A16207", // gold accent / price / links
          light: "#C68A2E",
          dark: "#854D0E", // button bg (white text ≥4.5:1)
        },
        ink: {
          DEFAULT: "#1C1917", // near-black headings / dark surfaces
          soft: "#292524",
        },
        paper: "#FAFAF9", // page background
        line: "#E7E5E4", // hairline borders
        muted: "#57534E", // secondary text
      },
      fontFamily: {
        sans: ["var(--font-almarai)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(28 25 23 / 0.04), 0 1px 3px 0 rgb(28 25 23 / 0.06)",
        lift: "0 10px 30px -12px rgb(28 25 23 / 0.18)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
