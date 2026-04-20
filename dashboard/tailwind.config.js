/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        paper: "#ffffff",
        line: "#d4d4d4",
        guard: "#159947",
        alert: "#dc2626",
        amber: "#d97706",
        cyanmark: "#0891b2"
      }
    }
  },
  plugins: []
};

