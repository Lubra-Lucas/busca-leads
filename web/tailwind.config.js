/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        plane: '#0d0d0d',
        surface: '#1a1a19',
        raised: '#232321',
        line: '#2c2c2a',
        axis: '#383835',
        ink: { DEFAULT: '#f0efec', soft: '#c3c2b7', muted: '#898781' },
        garnet: { DEFAULT: '#e0425c', deep: '#9b1b30' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
