/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // HisseRadar marka renkleri
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // Borsa renkleri
        up: '#22c55e',      // Yeşil - Yükseliş
        down: '#ef4444',    // Kırmızı - Düşüş
        neutral: '#6b7280', // Gri - Yatay
        // UI renkleri - daha yüksek kontrast
        surface: '#1e293b',  // Koyu mavi-gri arka plan
        card: '#334155',     // Kart arka planı
        border: '#475569',   // Kenar rengi
        muted: '#cbd5e1',    // Soluk metin - daha açık
        accent: '#3b82f6',   // Vurgu rengi
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
