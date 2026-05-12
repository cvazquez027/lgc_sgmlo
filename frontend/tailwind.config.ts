import type { Config } from "tailwindcss";

const config: Config = {
  // CRÍTICO: Aquí le decimos a Tailwind en qué carpetas buscar nuestras clases
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Declaramos los colores aquí también como puente de compatibilidad (Fail-safe)
      colors: {
        lgc: {
          primary: "#007FA1",
          accent: "#90A224",
          tostado: "#E0D6C4",
        }
      },
    },
  },
  plugins: [],
};

export default config;