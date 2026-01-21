/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors using CSS variables for easy swapping
        brand: {
          primary: 'var(--brand-primary, #3B82F6)',
          secondary: 'var(--brand-secondary, #10B981)',
          accent: 'var(--brand-accent, #F59E0B)',
        },
        // Semantic colors
        surface: {
          DEFAULT: 'var(--surface, #ffffff)',
          muted: 'var(--surface-muted, #f8fafc)',
          inverse: 'var(--surface-inverse, #0f172a)',
        },
        content: {
          DEFAULT: 'var(--content, #1e293b)',
          muted: 'var(--content-muted, #64748b)',
          inverse: 'var(--content-inverse, #f8fafc)',
        },
      },
      fontFamily: {
        heading: ['var(--font-heading, Inter)', 'sans-serif'],
        body: ['var(--font-body, Inter)', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
