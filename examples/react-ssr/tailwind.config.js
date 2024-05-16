const defaultTheme = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./ui/**/*.{html,js,ts,jsx,tsx}"],
  theme: {},
  daisyui: {
    themes: ["light", "dark", "dracula", "retro", "business", "night"],
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("daisyui"),
  ],
};
