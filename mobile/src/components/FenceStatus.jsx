import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { colors, spacing, radius, type } from '../theme';

/**
 * The dial the employee reads before punching.
 *
 * It shows fence state plainly and, when they are outside, how far — so
 * somebody standing at the wrong gate knows to walk rather than tap again.
 * The wording never claims a punch *will* succeed: the server decides, and
 * promising an outcome we cannot guarantee erodes trust in the whole system.
 */
export default function FenceStatus({ acquiring, site, metresOutside, accuracy, ready }) {
  if (acquiring) {
    return (
      <View style={[styles.card, styles.neutral]}>
        <ActivityIndicator color={colors.accent} />
        <Text style={styles.title}>Finding your location…</Text>
        <Text style={styles.detail}>Step outside if you are inside the building.</Text>
      </View>
    );
  }

  if (!site) {
    return (
      <View style={[styles.card, styles.warn]}>
        <Text style={styles.title}>No warehouse nearby</Text>
        <Text style={styles.detail}>
          You are not close to any warehouse you are assigned to.
        </Text>
      </View>
    );
  }

  const distance =
    metresOutside >= 1000
      ? `${(metresOutside / 1000).toFixed(1)} km`
      : `${Math.round(metresOutside)} m`;

  return (
    <View style={[styles.card, ready ? styles.ok : styles.warn]}>
      <Text style={styles.site}>{site.name}</Text>
      <Text style={styles.title}>
        {ready ? 'You are at the warehouse' : `${distance} outside the boundary`}
      </Text>
      <Text style={styles.detail}>
        {ready
          ? `Location accurate to about ${Math.round(accuracy ?? 0)} m`
          : 'Move closer to the warehouse to clock in.'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg, padding: spacing(3), alignItems: 'center',
    borderWidth: 2, gap: spacing(0.5),
  },
  neutral: { backgroundColor: colors.surface, borderColor: colors.border },
  ok: { backgroundColor: 'rgba(16,185,129,0.12)', borderColor: colors.ok },
  warn: { backgroundColor: 'rgba(245,158,11,0.12)', borderColor: colors.warn },
  site: { ...type.small, textTransform: 'uppercase', letterSpacing: 1 },
  title: { ...type.title, textAlign: 'center' },
  detail: { ...type.small, textAlign: 'center' },
});
