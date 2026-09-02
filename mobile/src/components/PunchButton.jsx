import { Pressable, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { colors, spacing, radius } from '../theme';

/**
 * One big target. Disabled while outside the fence so the employee gets an
 * immediate answer instead of a round trip to a rejection — but the server
 * still validates every punch that does get sent.
 */
export default function PunchButton({ direction, enabled, busy, onPress }) {
  const label = direction === 'IN' ? 'Clock in' : 'Clock out';
  return (
    <Pressable
      style={[
        styles.button,
        direction === 'IN' ? styles.in : styles.out,
        (!enabled || busy) && styles.off,
      ]}
      onPress={onPress}
      disabled={!enabled || busy}
    >
      {busy ? (
        <ActivityIndicator color="#fff" size="large" />
      ) : (
        <Text style={styles.text}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    height: 132, borderRadius: radius.lg,
    alignItems: 'center', justifyContent: 'center', marginTop: spacing(3),
  },
  in: { backgroundColor: colors.ok },
  out: { backgroundColor: colors.accent },
  off: { opacity: 0.35 },
  text: { color: '#fff', fontSize: 28, fontWeight: '700' },
});
