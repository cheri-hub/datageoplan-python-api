/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        govbr: {
          primary: '#1351B4',
          secondary: '#0C326F',
          accent: '#2670E8',
          success: '#168821',
          warning: '#FFCD07',
          error: '#E52207',
        },
      },
    },
  },
  plugins: [],
}
