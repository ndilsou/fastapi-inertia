const defaultTheme = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./ui/**/*.{html,js,ts,jsx,tsx}"],
  theme: {},
  daisyui: {
    themes: ["dracula"],
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui")],
};
