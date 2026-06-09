/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#151a1f",
        panel: "#f8faf7",
        line: "#dce3dc",
        gain: "#12805c",
        loss: "#b42318",
        signal: "#2458d3"
      }
    }
  },
  plugins: []
};
