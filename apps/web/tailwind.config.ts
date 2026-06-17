import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ipe: {
          primary: '#1e40af',
          secondary: '#0d9488',
          accent: '#f59e0b',
          danger: '#dc2626',
          success: '#16a34a',
          warning: '#d97706',
          surface: '#f8fafc',
          'surface-alt': '#f1f5f9',
          border: '#e2e8f0',
          text: '#0f172a',
          'text-muted': '#64748b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
export default config;
