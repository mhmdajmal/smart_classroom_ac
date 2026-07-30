/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#090d16',
        surface: '#111827',
        'surface-glass': 'rgba(17, 24, 39, 0.65)',
        'surface-hover': 'rgba(31, 41, 55, 0.8)',
        border: 'rgba(255, 255, 255, 0.08)',
        accent: {
          blue: '#3b82f6',
          cyan: '#06b6d4',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          purple: '#a855f7',
        },
      },
      backdropBlur: {
        xs: '2px',
        md: '12px',
        xl: '24px',
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        glow: '0 0 20px rgba(59, 130, 246, 0.25)',
        'glow-emerald': '0 0 20px rgba(16, 185, 129, 0.25)',
      },
    },
  },
  plugins: [],
};
