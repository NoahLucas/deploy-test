import CryptoKit
import Foundation
import HealthKit

struct SignalPayload: Encodable {
    let deviceId: String
    let collectedAt: Date
    let signals: [String: Double]
    let bundleId: String
    let appVersion: String
    let iosVersion: String
    let attestationToken: String?

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case collectedAt = "collected_at"
        case signals
        case bundleId = "bundle_id"
        case appVersion = "app_version"
        case iosVersion = "ios_version"
        case attestationToken = "attestation_token"
    }
}

enum RelayError: Error {
    case badHTTPStatus(Int)
    case noHealthData
}

final class SecureSignalRelay {
    private let healthStore = HKHealthStore()
    private let baseURL: URL
    private let relaySecret: String
    private let deviceId: String
    private let attestationTokenProvider: (() async throws -> String?)?

    init(
        baseURL: URL,
        relaySecret: String,
        deviceId: String,
        attestationTokenProvider: (() async throws -> String?)? = nil
    ) {
        self.baseURL = baseURL
        self.relaySecret = relaySecret
        self.deviceId = deviceId
        self.attestationTokenProvider = attestationTokenProvider
    }

    func sendDailySnapshot() async throws {
        let signals = try await collectSanitizedSignals()
        guard !signals.isEmpty else {
            throw RelayError.noHealthData
        }

        let bundleId = Bundle.main.bundleIdentifier ?? "unknown.bundle"
        let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0"
        let iosVersion = ProcessInfo.processInfo.operatingSystemVersionString
        let attestationToken = try await attestationTokenProvider?()

        let payload = SignalPayload(
            deviceId: deviceId,
            collectedAt: Date(),
            signals: signals,
            bundleId: bundleId,
            appVersion: appVersion,
            iosVersion: iosVersion,
            attestationToken: attestationToken
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let body = try encoder.encode(payload)

        let timestamp = String(Int(Date().timeIntervalSince1970))
        let nonce = UUID().uuidString.lowercased()
        let signature = makeSignature(body: body, timestamp: timestamp, nonce: nonce)

        var request = URLRequest(url: baseURL.appendingPathComponent("/api/v1/apple/ingest"))
        request.httpMethod = "POST"
        request.httpBody = body
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(timestamp, forHTTPHeaderField: "X-Relay-Timestamp")
        request.setValue(nonce, forHTTPHeaderField: "X-Relay-Nonce")
        request.setValue(signature, forHTTPHeaderField: "X-Relay-Signature")
        request.setValue(bundleId, forHTTPHeaderField: "X-Apple-Bundle-ID")
        request.setValue(appVersion, forHTTPHeaderField: "X-Apple-App-Version")
        request.setValue(iosVersion, forHTTPHeaderField: "X-Apple-IOS-Version")

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else { return }
        guard (200..<300).contains(httpResponse.statusCode) else {
            throw RelayError.badHTTPStatus(httpResponse.statusCode)
        }
    }

    // Replace this stub with real HealthKit queries and local aggregation.
    private func collectSanitizedSignals() async throws -> [String: Double] {
        return [
            "sleep_hours": 7.4,
            "resting_hr": 58,
            "steps": 9300,
            "mindful_minutes": 22,
            "deep_work_minutes": 185,
            "screen_time_hours": 5.1
        ]
    }

    private func makeSignature(body: Data, timestamp: String, nonce: String) -> String {
        var material = Data("\(timestamp).\(nonce).".utf8)
        material.append(body)

        let key = SymmetricKey(data: Data(relaySecret.utf8))
        let digest = HMAC<SHA256>.authenticationCode(for: material, using: key)
        return digest.hexString
    }
}

private extension Digest {
    var hexString: String {
        self.map { String(format: "%02x", $0) }.joined()
    }
}
