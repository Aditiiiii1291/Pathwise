/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F0F7FF',
          100: '#E0EFFF',
          200: '#BAE0FF',
          300: '#7CC4FA',
          400: '#38A4F4',
          500: '#0E86D4',
          600: '#026AA7',
          700: '#045486',
          800: '#08476F',
          900: '#0C3C5D',
        },
        risk: {
          low: '#10B981',
          'low-bg': '#ECFDF5',
          'low-border': '#A7F3D0',
          'low-text': '#065F46',

          medium: '#F59E0B',
          'medium-bg': '#FFFBEB',
          'medium-border': '#FDE68A',
          'medium-text': '#92400E',

          high: '#F97316',
          'high-bg': '#FFF7ED',
          'high-border': '#FED7AA',
          'high-text': '#9A3412',

          critical: '#EF4444',
          'critical-bg': '#FEF2F2',
          'critical-border': '#FECACA',
          'critical-text': '#991B1B',
        },
        trend: {
          improving: '#10B981',
          'improving-bg': '#ECFDF5',
          stable: '#3B82F6',
          'stable-bg': '#EFF6FF',
          gradual: '#F59E0B',
          'gradual-bg': '#FFFBEB',
          rapid: '#EF4444',
          'rapid-bg': '#FEF2F2',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02)',
        'card': '0 2px 6px 0 rgba(0, 0, 0, 0.03), 0 1px 3px 0 rgba(0, 0, 0, 0.02)',
        'hover': '0 4px 12px 0 rgba(0, 0, 0, 0.05), 0 2px 4px 0 rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}
