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
        brand: {
          DEFAULT: "#6b4226",
          light: "#a9744f",
          dark: "#3f2417",
        },
      },
    },
  },
  plugins: [],
};

export default config;
