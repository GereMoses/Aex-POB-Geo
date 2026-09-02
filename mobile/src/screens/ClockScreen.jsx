import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, RefreshControl, Alert, Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, ApiError } from '../api/client';
import { buildPunchPayload } from '../api/punchPayload';
import { useAuth } from '../auth/AuthContext';
import { useLocationTracker, PermissionState } from '../location/useLocationTracker';
import { nearestSite, willLikelyPass } from '../location/geo';
import { collectIntegrity, blockingHint } from '../integrity/integrity';
import { captureSelfie, SelfieCancelled } from '../camera/selfie';
import { MIN_BURST_SAMPLES } from '../config';
import FenceStatus from '../components/FenceStatus';
import PunchButton from '../components/PunchButton';
import { colors, spacing, radius, type } from '../theme';

export default function ClockScreen() {
  const { signOut, handleUnauthenticated } = useAuth();
  const [sites, setSites] = useState([]);
  const [loadingSites, setLoadingSites] = useState(true);
  const [busy, setBusy] = useState(false);
  const [lastPunch, setLastPunch] = useState(null);
  const [notice, setNotice] = useState(null);

  const {
    permission, position, error: locationError, sawMockProvider,
    getBurst, getApproachPath,
  } = useLocationTracker(true);

  const loadSites = useCallback(async () => {
    setLoadingSites(true);
    try {
      const result = await api.mySites();
      setSites(result?.sites ?? []);
      setNotice(null);
    } catch (e) {
      if (e.status === 401) handleUnauthenticated();
      else setNotice(e.message);
    } finally {
      setLoadingSites(false);
    }
  }, [handleUnauthenticated]);

  useEffect(() => { loadSites(); }, [loadSites]);

  const { site, metresOutside } = useMemo(
    () => nearestSite(position, sites), [position, sites],
  );
  const ready = willLikelyPass(position, site, metresOutside);

  const punch = async (direction) => {
    if (!position) return;
    setBusy(true);
    setNotice(null);
    try {
      const integrity = await collectIntegrity({ sawMockProvider });

      // Warn before spending the employee's time on a photo and a round trip
      // the server is certain to refuse.
      const hint = blockingHint(integrity);
      if (hint) {
        setNotice(hint);
        return;
      }

      let selfie = null;
      if (site?.require_selfie) {
        try {
          selfie = await captureSelfie();
        } catch (e) {
          if (e instanceof SelfieCancelled) return;
          throw e;
        }
      }

      const result = await api.punch(
        direction,
        buildPunchPayload({
          position,
          samples: getBurst(),
          approachPath: getApproachPath(),
          integrity,
          selfieBase64: selfie,
        }),
      );

      setLastPunch({
        direction,
        at: new Date(result.timestamp),
        site: result.zone?.name,
        pendingReview: result.photo_pending_review,
      });
      Alert.alert(
        direction === 'IN' ? 'Clocked in' : 'Clocked out',
        result.message,
      );
    } catch (e) {
      if (e.status === 401) {
        handleUnauthenticated();
      } else if (e instanceof ApiError) {
        // The server writes refusal messages for the employee; show them as-is
        // rather than inventing our own wording for a rule we did not evaluate.
        Alert.alert('Not clocked in', e.message);
        setNotice(e.message);
      } else {
        Alert.alert('Something went wrong', e.message ?? 'Please try again.');
      }
    } finally {
      setBusy(false);
    }
  };

  const acquiring = permission === PermissionState.PENDING || (!position && !locationError);
  const thinSamples = position && getBurst().length < MIN_BURST_SAMPLES;

  if (permission === PermissionState.BLOCKED) {
    return (
      <SafeAreaView style={styles.root}>
        <View style={styles.blocked}>
          <Text style={type.title}>Location is turned off</Text>
          <Text style={styles.blockedText}>
            Apex Clock needs your location to confirm you are at your warehouse.
            Turn it on in your phone settings, then reopen the app.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={loadingSites} onRefresh={loadSites} tintColor={colors.accent} />
        }
      >
        <View style={styles.header}>
          <Text style={type.title}>Apex Clock</Text>
          <Pressable onPress={signOut} hitSlop={12}>
            <Text style={styles.signOut}>Sign out</Text>
          </Pressable>
        </View>

        <FenceStatus
          acquiring={acquiring}
          site={site}
          metresOutside={metresOutside}
          accuracy={position?.accuracy}
          ready={ready}
        />

        {notice ? <Text style={styles.notice}>{notice}</Text> : null}
        {locationError ? <Text style={styles.notice}>{locationError}</Text> : null}

        {/* Below three fixes the server skips its drift check entirely, so the
            punch is weaker evidence. Worth a quiet nudge, not a block. */}
        {thinSamples && !acquiring ? (
          <Text style={styles.hint}>Hold on a moment while the signal settles…</Text>
        ) : null}

        {site?.require_selfie ? (
          <Text style={styles.hint}>This warehouse asks for a photo when you clock in.</Text>
        ) : null}

        <PunchButton direction="IN" enabled={ready} busy={busy} onPress={() => punch('IN')} />
        <PunchButton direction="OUT" enabled={ready} busy={busy} onPress={() => punch('OUT')} />

        {lastPunch ? (
          <View style={styles.receipt}>
            <Text style={styles.receiptTitle}>
              {lastPunch.direction === 'IN' ? 'Clocked in' : 'Clocked out'} at{' '}
              {lastPunch.at.toLocaleTimeString()}
            </Text>
            <Text style={type.small}>{lastPunch.site}</Text>
            {lastPunch.pendingReview ? (
              <Text style={type.small}>Your photo will be checked by your supervisor.</Text>
            ) : null}
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(2.5), paddingBottom: spacing(6) },
  header: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: spacing(3),
  },
  signOut: { color: colors.textMuted, fontSize: 15 },
  notice: {
    color: colors.warn, marginTop: spacing(2), textAlign: 'center', fontSize: 15,
  },
  hint: { ...type.small, textAlign: 'center', marginTop: spacing(1.5) },
  blocked: { flex: 1, justifyContent: 'center', padding: spacing(4), gap: spacing(1.5) },
  blockedText: { ...type.small, lineHeight: 21 },
  receipt: {
    marginTop: spacing(4), padding: spacing(2), borderRadius: radius.md,
    backgroundColor: colors.surface, alignItems: 'center', gap: spacing(0.5),
  },
  receiptTitle: { ...type.body, fontWeight: '600' },
});
