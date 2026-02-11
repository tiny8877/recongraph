/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0e17',
          secondary: '#111827',
          card: '#1a1f2e',
          hover: '#242938',
          elevated: '#1e2640',
        },
        accent: {
          cyan: '#00ffff',
          'cyan-dim': '#00cccc',
          blue: '#00aaff',
          'blue-dim': '#0088cc',
          green: '#00ff88',
          'green-dim': '#00cc66',
          yellow: '#ffff00',
          red: '#ff4444',
          orange: '#ff8800',
          purple: '#aa00ff',
          pink: '#ff0066',
          teal: '#00d4aa',
        },
        border: {
          dark: '#1e293b',
          medium: '#2d3748',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
