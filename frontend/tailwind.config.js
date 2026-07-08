module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card-bg)",
        cardBorder: "var(--card-border)",
        textMuted: "var(--text-muted)",
        inputBg: "var(--input-bg)",
        inputBorder: "var(--input-border)",
        primary: {
          DEFAULT: "#6366f1",
          hover: "#4f46e5",
        },
        secondary: {
          DEFAULT: "#8b5cf6",
          hover: "#7c3aed",
        },
        accent: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
      },
      fontSize: {
        xxs: ['0.625rem', { lineHeight: '0.875rem' }],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
