/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: {
          50: '#faf7f0',
          100: '#f4e8d0',
          200: '#e8dcc0',
          300: '#ddd4b8',
          400: '#d2c8b0',
          500: '#c4b89a',
          600: '#b8a88a',
          700: '#8b7355',
          800: '#6b5639',
          900: '#4a3d28',
        },
        ink: {
          50: '#f5f3f0',
          100: '#e8e0d6',
          200: '#d4c8b8',
          300: '#b8a88a',
          400: '#8b7355',
          500: '#6b5639',
          600: '#4a3d28',
          700: '#3d2817',
          800: '#2d1f12',
          900: '#1a1209',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
