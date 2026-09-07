/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: { DEFAULT: "#2d6a4f", dark: "#1b4332" },
        stress: "#e08e45",
        severe: "#c1121f",
      },
    },
  },
  plugins: [],
};
