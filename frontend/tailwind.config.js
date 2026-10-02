/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          primary: '#09090b',
          card: '#111318',
          hover: '#1c1f26',
        },
        border: {
          default: '#1e1e1e',
          subtle: '#161616',
        },
        accent: {
          positive: '#00dc82',
          negative: '#ef4444',
          neutral: '#00dc82',
          warning: '#f59e0b',
        },
        text: {
          primary: '#e4e4e7',
          secondary: '#a1a1aa',
          muted: '#52525b',
        },
      },
      fontFamily: {
        sans: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
