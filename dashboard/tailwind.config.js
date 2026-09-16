/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#050509',
        surface: '#0b0d14',
        ink: '#f5f7ff',
        muted: '#8b93a7',
        cyan: '#00f5ff',
        pink: '#ff2bd6',
        purple: '#8a2be2',
        green: '#39ff88',
        warn: '#ffe600',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
