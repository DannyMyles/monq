import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        cream: {
          DEFAULT: "#F3EEE4",
          card: "#FBF8F2",
        },
        ink: {
          DEFAULT: "#2A241E",
          light: "#5C5347",
          muted: "#8A8175",
        },
        accent: {
          DEFAULT: "#DD8A2E",
          light: "#F3D9A6",
          dark: "#B96F1F",
        },
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-geist-sans)", "Arial", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
  plugins: [],
};
export default config;
