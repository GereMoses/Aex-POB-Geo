/**
 * Visual tokens.
 *
 * Deliberately high-contrast and large-touch: this is used outdoors, in
 * sunlight, often in gloves, by people who want to be through the gate.
 */
export const colors = {
  bg: '#0F172A',
  surface: '#1E293B',
  surfaceAlt: '#334155',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  ok: '#10B981',
  warn: '#F59E0B',
  bad: '#EF4444',
  accent: '#0EA5E9',
  border: '#334155',
};

export const spacing = (n) => n * 8;

export const radius = { sm: 8, md: 12, lg: 20, pill: 999 };

export const type = {
  display: { fontSize: 34, fontWeight: '700', color: colors.text },
  title: { fontSize: 20, fontWeight: '600', color: colors.text },
  body: { fontSize: 16, color: colors.text },
  small: { fontSize: 13, color: colors.textMuted },
};
