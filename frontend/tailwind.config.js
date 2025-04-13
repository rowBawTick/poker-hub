/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'poker-green': '#1a5336',
        'poker-red': '#b91c1c',
        'poker-blue': '#1e40af',
        'poker-black': '#171717',
      },
    },
  },
  plugins: [],
};
