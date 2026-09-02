import { useState } from 'react';
import {
  Text, TextInput, Pressable, StyleSheet, ActivityIndicator,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { colors, spacing, radius, type } from '../theme';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      await signIn(username.trim(), password);
    } catch (e) {
      setError(e.message || 'Could not sign in.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Text style={styles.brand}>Apex Clock</Text>
      <Text style={styles.sub}>Sign in with your employee number</Text>

      <TextInput
        style={styles.input}
        placeholder="Employee number"
        placeholderTextColor={colors.textMuted}
        autoCapitalize="characters"
        autoCorrect={false}
        value={username}
        onChangeText={setUsername}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor={colors.textMuted}
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        onSubmitEditing={submit}
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable
        style={[styles.button, (busy || !username || !password) && styles.buttonOff]}
        onPress={submit}
        disabled={busy || !username || !password}
      >
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Sign in</Text>}
      </Pressable>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg, padding: spacing(3), justifyContent: 'center' },
  brand: { ...type.display, textAlign: 'center' },
  sub: { ...type.small, textAlign: 'center', marginBottom: spacing(4) },
  input: {
    backgroundColor: colors.surface, color: colors.text,
    borderRadius: radius.md, padding: spacing(2), fontSize: 17,
    marginBottom: spacing(1.5), borderWidth: 1, borderColor: colors.border,
  },
  error: { color: colors.bad, marginBottom: spacing(1.5), textAlign: 'center' },
  button: {
    backgroundColor: colors.accent, borderRadius: radius.md,
    padding: spacing(2), alignItems: 'center', marginTop: spacing(1),
  },
  buttonOff: { opacity: 0.4 },
  buttonText: { color: '#fff', fontSize: 17, fontWeight: '600' },
});
