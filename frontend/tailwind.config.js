/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: 'var(--font-sans)',
        heading: 'var(--font-heading)',
      },
      colors: {
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        'primary-hover': 'rgb(var(--color-primary-hover) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        'input-bg': 'rgb(var(--color-input-bg) / <alpha-value>)',
        'text-primary': 'rgb(var(--color-text-primary) / <alpha-value>)',
        'chart-a': 'rgb(var(--chart-a) / <alpha-value>)',
        'chart-ptr': 'rgb(var(--chart-ptr) / <alpha-value>)',
        'chart-soa': 'rgb(var(--chart-soa) / <alpha-value>)',
        'chart-srv': 'rgb(var(--chart-srv) / <alpha-value>)',
        'chart-txt': 'rgb(var(--chart-txt) / <alpha-value>)',
        'chart-zone': 'rgb(var(--chart-zone) / <alpha-value>)',
      },
    },
  },
  plugins: [],
};
