import SwiftUI

struct ControlCenterView: View {
    @AppStorage("admin_token") private var adminToken: String = ""
    @State private var prioritiesText: String = "Ship one note\nReview endpoint toggles"
    @State private var risksText: String = "Context switching"
    @State private var contextText: String = "Focus on brand authority and shipping cadence."

    @State private var toggles: [EndpointToggleItem] = []
    @State private var dailyBrief: LabDailyBriefResponse?
    @State private var sqEvents: [SquarespaceEventItem] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        List {
            Section("Admin") {
                TextField("X-Admin-Token", text: $adminToken)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                Text("Stored locally on this device.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("Endpoint Toggles") {
                if toggles.isEmpty {
                    Text("No toggle data loaded.")
                        .foregroundStyle(.secondary)
                }
                ForEach(toggles) { item in
                    Toggle(isOn: Binding(
                        get: { item.enabled },
                        set: { newValue in
                            Task { await updateToggle(path: item.path, enabled: newValue) }
                        }
                    )) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.path)
                                .font(.caption)
                            Text(item.platform.uppercased())
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                Button("Refresh Toggles") {
                    Task { await loadToggles() }
                }
            }

            Section("Daily Brief") {
                TextField("Priorities (newline separated)", text: $prioritiesText, axis: .vertical)
                    .lineLimit(3...6)
                TextField("Risks (newline separated)", text: $risksText, axis: .vertical)
                    .lineLimit(2...4)
                TextField("Context", text: $contextText, axis: .vertical)
                    .lineLimit(2...5)
                Button("Generate Brief") {
                    Task { await generateBrief() }
                }
                if let dailyBrief {
                    Text(dailyBrief.headline)
                        .font(.headline)
                    ForEach(dailyBrief.topActions, id: \.self) { action in
                        Text("• \(action)")
                            .font(.caption)
                    }
                }
            }

            Section("Squarespace Events") {
                Button("Refresh Events") {
                    Task { await loadSquarespaceEvents() }
                }
                ForEach(sqEvents.prefix(8)) { item in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(item.eventType)
                            .font(.caption)
                        Text(item.eventId)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            if let errorMessage {
                Section("Status") {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Control Center")
        .overlay {
            if isLoading {
                ProgressView()
            }
        }
        .task {
            await loadAll()
        }
    }

    @MainActor
    private func loadAll() async {
        await loadToggles()
        await loadSquarespaceEvents()
    }

    @MainActor
    private func loadToggles() async {
        guard !adminToken.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await BackendClient.shared.listEndpointToggles(adminToken: adminToken)
            toggles = response.items
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func updateToggle(path: String, enabled: Bool) async {
        guard !adminToken.isEmpty else { return }
        do {
            let response = try await BackendClient.shared.setEndpointToggle(
                path: path,
                enabled: enabled,
                adminToken: adminToken
            )
            toggles = response.items
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
            await loadToggles()
        }
    }

    @MainActor
    private func generateBrief() async {
        guard !adminToken.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let brief = try await BackendClient.shared.generateDailyBrief(
                priorities: splitLines(prioritiesText),
                risks: splitLines(risksText),
                context: contextText,
                adminToken: adminToken
            )
            dailyBrief = brief
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func loadSquarespaceEvents() async {
        guard !adminToken.isEmpty else { return }
        do {
            let response = try await BackendClient.shared.listSquarespaceEvents(adminToken: adminToken)
            sqEvents = response.items
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func splitLines(_ input: String) -> [String] {
        input
            .split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }
}
