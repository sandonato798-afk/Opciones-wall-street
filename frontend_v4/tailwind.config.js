/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0e16',
          surface: '#0f131b',
          card: '#131722',
          border: '#1f2633',
          borderHighlight: '#2c3547',
          accent: '#00e676', // Verde institucional primas / profit
          accentDim: '#00c853',
          danger: '#ff3d57', // Alertas protocolo 15:55 / ITM
          warning: '#ffb300', // Break-even / alertas intermedias
          cyan: '#00e5ff', // Griegas / Delta
          muted: '#7e8b9b',
        }
      },
      fontFamily: {
        mono: ['"Space Grotesk"', 'monospace', 'ui-monospace'],
      }
    },
  },
  plugins: [],
}
