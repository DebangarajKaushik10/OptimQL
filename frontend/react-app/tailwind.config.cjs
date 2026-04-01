const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', ...defaultTheme.fontFamily.sans],
        mono: ['"JetBrains Mono"', ...defaultTheme.fontFamily.mono],
      },
      colors: {
        space: '#080C14',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(300%) skew(-20deg)' },
        }
      }
    },
  },
  plugins: [],
}
