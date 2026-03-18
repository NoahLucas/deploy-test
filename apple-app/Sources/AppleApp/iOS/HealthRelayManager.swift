import CryptoKit
import Foundation
import HealthKit

@MainActor
final class HealthRelayManager: ObservableObject {
    enum SyncState: Equatable {
        case idle
        case syncing
        case success(String)
        case failure(String)
    }

    @Published private(set) var healthDataAvailable = HKHealthStore.isHealthDataAvailable()
    @Published private(set) var authorizationGranted = false
    @Published private(set) var syncState: SyncState = .idle
    @Published private(set) var lastHeartRateBPM: Int?
    @Published private(set) var lastHeartRateAt: Date?

    private let healthStore = HKHealthStore()

    private var readTypes: Set<HKObjectType> {
        var result: Set<HKObjectType> = []
        if let heartRate = HKObjectType.quantityType(forIdentifier: .heartRate) {
            result.insert(heartRate)
        }
        if let restingHeartRate = HKObjectType.quantityType(forIdentifier: .restingHeartRate) {
            result.insert(restingHeartRate)
        }
        return result
    }

    func refreshAuthorizationStatus() async {
        guard healthDataAvailable else {
            authorizationGranted = false
            return
        }

        let statuses = readTypes.compactMap { type -> HKAuthorizationStatus? in
            guard let quantityType = type as? HKQuantityType else { return nil }
            return healthStore.authorizationStatus(for: quantityType)
        }
        authorizationGranted = statuses.contains(.sharingAuthorized)
        await refreshLatestHeartRatePreview()
    }

    func requestAuthorization() async {
        guard healthDataAvailable else {
            syncState = .failure("Health data is not available on this device.")
            return
        }

        do {
            try await healthStore.requestAuthorization(toShare: [], read: readTypes)
            await refreshAuthorizationStatus()
            syncState = authorizationGranted ? .success("Health access granted.") : .failure("Health access was not granted.")
        } catch {
            syncState = .failure(error.localizedDescription)
        }
    }

    func syncNow(baseURLString: String, relaySecret: String, deviceId: String) async {
        guard healthDataAvailable else {
            syncState = .failure("Health data is not available on this device.")
            return
        }
        guard authorizationGranted else {
            syncState = .failure("Grant Health access first.")
            return
        }
        guard let baseURL = URL(string: baseURLString), !relaySecret.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            syncState = .failure("Set a valid backend URL and relay secret.")
            return
        }
        let normalizedDeviceID = deviceId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard normalizedDeviceID.count >= 6 else {
            syncState = .failure("Set a stable device ID with at least 6 characters.")
            return
        }

        syncState = .syncing

        do {
            let relay = SecureSignalRelay(
                healthStore: healthStore,
                baseURL: baseURL,
                relaySecret: relaySecret,
                deviceId: normalizedDeviceID
            )
            try await relay.sendDailySnapshot()
            await refreshLatestHeartRatePreview()
            if let bpm = lastHeartRateBPM {
                syncState = .success("Synced \(bpm) BPM to the website backend.")
            } else {
                syncState = .success("Health snapshot synced.")
            }
        } catch {
            syncState = .failure(error.localizedDescription)
        }
    }

    private func refreshLatestHeartRatePreview() async {
        do {
            let sample = try await latestQuantitySample(identifier: .heartRate, sinceHours: 24)
            if let sample {
                lastHeartRateBPM = Int(round(sample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))))
                lastHeartRateAt = sample.endDate
            } else {
                lastHeartRateBPM = nil
                lastHeartRateAt = nil
            }
        } catch {
            lastHeartRateBPM = nil
            lastHeartRateAt = nil
        }
    }

    private func latestQuantitySample(
        identifier: HKQuantityTypeIdentifier,
        sinceHours: Double
    ) async throws -> HKQuantitySample? {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: identifier) else {
            return nil
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: Date().addingTimeInterval(-(sinceHours * 60 * 60)),
            end: Date(),
            options: .strictStartDate
        )
        let sortDescriptors = [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: quantityType,
                predicate: predicate,
                limit: 1,
                sortDescriptors: sortDescriptors
            ) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: samples?.first as? HKQuantitySample)
            }

            healthStore.execute(query)
        }
    }
}

private struct SignalPayload: Encodable {
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

private enum RelayError: LocalizedError {
    case badHTTPStatus(Int)
    case noHealthData

    var errorDescription: String? {
        switch self {
        case .badHTTPStatus(let code):
            return "Relay rejected the snapshot with HTTP \(code)."
        case .noHealthData:
            return "No recent HealthKit heart-rate data was found."
        }
    }
}

private final class SecureSignalRelay {
    private let healthStore: HKHealthStore
    private let baseURL: URL
    private let relaySecret: String
    private let deviceId: String
    private let attestationTokenProvider: (() async throws -> String?)?

    init(
        healthStore: HKHealthStore,
        baseURL: URL,
        relaySecret: String,
        deviceId: String,
        attestationTokenProvider: (() async throws -> String?)? = nil
    ) {
        self.healthStore = healthStore
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

    private func collectSanitizedSignals() async throws -> [String: Double] {
        var signals: [String: Double] = [:]

        if let latestHeartRate = try await latestHeartRateBPM() {
            signals["heart_rate_bpm"] = latestHeartRate
        }

        if let restingHeartRate = try await latestRestingHeartRateBPM() {
            signals["resting_hr"] = restingHeartRate
        }

        return signals
    }

    private func latestHeartRateBPM() async throws -> Double? {
        try await latestQuantityValue(
            identifier: .heartRate,
            unit: HKUnit.count().unitDivided(by: .minute()),
            sinceHours: 24
        )
    }

    private func latestRestingHeartRateBPM() async throws -> Double? {
        try await latestQuantityValue(
            identifier: .restingHeartRate,
            unit: HKUnit.count().unitDivided(by: .minute()),
            sinceHours: 72
        )
    }

    private func latestQuantityValue(
        identifier: HKQuantityTypeIdentifier,
        unit: HKUnit,
        sinceHours: Double
    ) async throws -> Double? {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: identifier) else {
            return nil
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: Date().addingTimeInterval(-(sinceHours * 60 * 60)),
            end: Date(),
            options: .strictStartDate
        )
        let sortDescriptors = [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: quantityType,
                predicate: predicate,
                limit: 1,
                sortDescriptors: sortDescriptors
            ) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }

                guard let sample = samples?.first as? HKQuantitySample else {
                    continuation.resume(returning: nil)
                    return
                }

                continuation.resume(returning: sample.quantity.doubleValue(for: unit))
            }

            healthStore.execute(query)
        }
    }

    private func makeSignature(body: Data, timestamp: String, nonce: String) -> String {
        var material = Data("\(timestamp).\(nonce).".utf8)
        material.append(body)

        let key = SymmetricKey(data: Data(relaySecret.utf8))
        let digest = HMAC<SHA256>.authenticationCode(for: material, using: key)
        return digest.map { String(format: "%02x", $0) }.joined()
    }
}
