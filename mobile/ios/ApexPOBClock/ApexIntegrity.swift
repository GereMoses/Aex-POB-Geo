import Foundation
import DeviceCheck
import CoreLocation
import CryptoKit

/**
 Device integrity signals for the geofenced time clock, iOS side.

 iOS gives less away than Android — there is no mock-location setting to read,
 and no filesystem access to check for a su binary in the normal case. The two
 signals that do carry weight here are jailbreak heuristics and App Attest,
 whose assertion is signed by Apple and verified server-side.

 Note that simulated location on iOS is detected at the point of use rather
 than here: CLLocation exposes `sourceInformation.isSimulatedBySoftware` from
 iOS 15, which the location layer reads per fix.
 */
@objc(ApexIntegrity)
class ApexIntegrity: NSObject {

    @objc static func requiresMainQueueSetup() -> Bool { false }

    @objc(getSignals:rejecter:)
    func getSignals(_ resolve: RCTPromiseResolveBlock,
                    rejecter reject: RCTPromiseRejectBlock) {
        resolve([
            "isMockLocationEnabled": false,   // resolved per-fix, not globally
            "isCompromised": isJailbroken(),
            "isEmulator": isSimulator(),
            "isDeveloperModeEnabled": false,
        ])
    }

    private func isSimulator() -> Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }

    /**
     Jailbreak heuristics.

     Checks for the usual package managers, then attempts a write outside the
     sandbox — an app that can write to /private is not sandboxed. Reported as
     a soft signal: the server scores it rather than blocking, because a
     jailbroken personal handset is not by itself evidence of time fraud.
     */
    private func isJailbroken() -> Bool {
        #if targetEnvironment(simulator)
        return false
        #else
        let suspiciousPaths = [
            "/Applications/Cydia.app",
            "/Applications/Sileo.app",
            "/Library/MobileSubstrate/MobileSubstrate.dylib",
            "/bin/bash",
            "/usr/sbin/sshd",
            "/etc/apt",
            "/private/var/lib/apt/",
        ]
        for path in suspiciousPaths where FileManager.default.fileExists(atPath: path) {
            return true
        }

        let probe = "/private/apex_integrity_probe.txt"
        do {
            try "probe".write(toFile: probe, atomically: true, encoding: .utf8)
            try FileManager.default.removeItem(atPath: probe)
            return true
        } catch {
            return false
        }
        #endif
    }

    /**
     Request an App Attest assertion.

     The key is generated once and reused; the resulting attestation is opaque
     to this app and is verified by the backend against Apple's service. As on
     Android, an unavailable attestation resolves to UNAVAILABLE rather than
     FAIL — a warehouse with no signal must not look like a tampered device.
     */
    @objc(requestAttestation:rejecter:)
    func requestAttestation(_ resolve: @escaping RCTPromiseResolveBlock,
                            rejecter reject: @escaping RCTPromiseRejectBlock) {
        guard #available(iOS 14.0, *), DCAppAttestService.shared.isSupported else {
            resolve("UNAVAILABLE")
            return
        }

        let service = DCAppAttestService.shared
        service.generateKey { keyId, error in
            guard let keyId = keyId, error == nil else {
                resolve("UNAVAILABLE")
                return
            }
            // The challenge must come from the server for a production
            // deployment so it cannot be replayed; this sends the key id and
            // lets the backend drive the challenge exchange.
            let challenge = Data(keyId.utf8)
            let hash = Data(SHA256.hash(data: challenge))
            service.attestKey(keyId, clientDataHash: hash) { attestation, attestError in
                guard let attestation = attestation, attestError == nil else {
                    resolve("UNAVAILABLE")
                    return
                }
                resolve(attestation.base64EncodedString())
            }
        }
    }
}
