import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#2563EB",
          deep: "#1D4ED8",
          glow: "#DBEAFE",
        },
        ink: "#0F172A",
        mist: "#F8FAFC",
        success: "#ECFDF5",
        danger: "#FEF2F2",
      },
      fontFamily: {
        heading: ["Manrope", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      boxShadow: {
        panel: "0 4px 20px rgba(0,0,0,0.03)",
        active: "0 8px 30px rgba(37,99,235,0.12)",
        float: "0 20px 60px rgba(15,23,42,0.08)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)",
      },
      keyframes: {
        drift: {
          "0%, 100%": { transform: "translate3d(0, 0, 0)" },
          "50%": { transform: "translate3d(0, -14px, 0)" },
        },
        rise: {
          "0%": { opacity: "0", transform: "translate3d(0, 18px, 0)" },
          "100%": { opacity: "1", transform: "translate3d(0, 0, 0)" },
        },
      },
      animation: {
        drift: "drift 8s ease-in-out infinite",
        rise: "rise 600ms ease forwards",
      },
    },
  },
  plugins: [],
};

export default config;
