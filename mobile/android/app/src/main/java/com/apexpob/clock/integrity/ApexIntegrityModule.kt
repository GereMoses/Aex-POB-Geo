package com.apexpob.clock.integrity

import android.os.Build
import android.provider.Settings
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest
import java.io.File

/**
 * Device integrity signals for the geofenced time clock.
 *
 * None of this is tamper-proof on its own — a determined attacker with root
 * can defeat every local check here. That is precisely why Play Integrity is
 * included: its verdict is signed by Google and evaluated server-side, so it
 * is the one signal a patched client cannot simply fabricate.
 */
class ApexIntegrityModule(private val reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName() = "ApexIntegrity"

    @ReactMethod
    fun getSignals(promise: Promise) {
        try {
            val signals = Arguments.createMap().apply {
                putBoolean("isMockLocationEnabled", isMockLocationAppSelected())
                putBoolean("isCompromised", isRooted())
                putBoolean("isEmulator", isProbablyEmulator())
                putBoolean("isDeveloperModeEnabled", isDeveloperModeEnabled())
            }
            promise.resolve(signals)
        } catch (e: Exception) {
            promise.reject("INTEGRITY_ERROR", e.message, e)
        }
    }

    /**
     * Whether a mock-location app is configured in Developer Options.
     *
     * ALLOW_MOCK_LOCATION was deprecated in API 23; from Marshmallow onwards
     * the selected app is what matters, and individual fixes carry their own
     * mock flag which the JS layer reads from the location provider.
     */
    private fun isMockLocationAppSelected(): Boolean = try {
        // "mock_location" returns the string "0" when mock location is
        // DISABLED — not null, not empty. Testing it with isNotEmpty() reports
        // every device as mocked and refuses legitimate punches.
        val v = Settings.Secure.getString(reactContext.contentResolver, "mock_location")
        !v.isNullOrEmpty() && v != "0"
    } catch (e: Exception) {
        false
    }

    private fun isDeveloperModeEnabled(): Boolean = try {
        Settings.Global.getInt(
            reactContext.contentResolver,
            Settings.Global.DEVELOPMENT_SETTINGS_ENABLED,
            0,
        ) != 0
    } catch (e: Exception) {
        false
    }

    /**
     * Cheap root heuristics: a test-keys build, or the presence of a su binary
     * in any of the usual locations. Reported as a soft signal — plenty of
     * people root their own handset for reasons that have nothing to do with
     * attendance, so the server scores it rather than blocking on it.
     */
    private fun isRooted(): Boolean {
        if (Build.TAGS?.contains("test-keys") == true) return true
        val paths = arrayOf(
            "/system/app/Superuser.apk", "/sbin/su", "/system/bin/su",
            "/system/xbin/su", "/data/local/xbin/su", "/data/local/bin/su",
            "/system/sd/xbin/su", "/system/bin/failsafe/su", "/data/local/su",
            "/su/bin/su", "/system/xbin/daemonsu",
        )
        return paths.any { File(it).exists() }
    }

    private fun isProbablyEmulator(): Boolean =
        Build.FINGERPRINT.startsWith("generic") ||
            Build.FINGERPRINT.startsWith("unknown") ||
            Build.MODEL.contains("google_sdk") ||
            Build.MODEL.contains("Emulator") ||
            Build.MODEL.contains("Android SDK built for x86") ||
            Build.MANUFACTURER.contains("Genymotion") ||
            Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic") ||
            Build.PRODUCT == "google_sdk"

    /**
     * Request a Play Integrity token.
     *
     * The token is opaque here by design — it is meaningful only to Google's
     * decode API, which the backend calls with its own credentials. A client
     * that could interpret or forge it would defeat the purpose, so this
     * method resolves the raw token and lets the server reach the verdict.
     */
    @ReactMethod
    fun requestAttestation(promise: Promise) {
        try {
            val manager = IntegrityManagerFactory.create(reactContext)
            manager.requestIntegrityToken(
                IntegrityTokenRequest.builder()
                    .setCloudProjectNumber(CLOUD_PROJECT_NUMBER)
                    .build(),
            )
                .addOnSuccessListener { response -> promise.resolve(response.token()) }
                // Play Integrity needs network and Play Services. Neither being
                // available says nothing about tampering, so this resolves
                // UNAVAILABLE rather than failing the punch at a warehouse with
                // poor signal.
                .addOnFailureListener { promise.resolve("UNAVAILABLE") }
        } catch (e: Exception) {
            promise.resolve("UNAVAILABLE")
        }
    }

    companion object {
        // Replace with the Google Cloud project number linked to the Play
        // Console entry for this app.
        private const val CLOUD_PROJECT_NUMBER = 0L
    }
}
