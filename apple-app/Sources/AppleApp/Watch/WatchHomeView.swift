import SwiftUI

struct WatchHomeView: View {
    @State private var siteTitle = "noahlucas.com"
    @State private var status = "Tap refresh to check status."
    @State private var isLoading = false

    var body: some View {
        List {
            Section {
                HStack(alignment: .top, spacing: 8) {
                    if isLoading {
                        ProgressView()
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text(siteTitle)
                            .font(.headline)
                            .lineLimit(2)

                        Text(status)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section("Actions") {
                Button {
                    Task {
                        await refreshTitle()
                    }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(isLoading)

                Link(destination: SiteConfiguration.websiteURL) {
                    Label("Open Website", systemImage: "safari")
                }
            }
        }
        .navigationTitle("Noah")
        .task {
            await refreshTitle()
        }
    }

    @MainActor
    private func refreshTitle() async {
        isLoading = true
        defer { isLoading = false }

        do {
            var request = URLRequest(url: SiteConfiguration.websiteURL)
            request.timeoutInterval = 12

            let (data, _) = try await URLSession.shared.data(for: request)
            let html = String(decoding: data.prefix(120_000), as: UTF8.self)
            siteTitle = HTMLTitleParser.extractTitle(from: html) ?? "noahlucas.com"
            status = "Updated \(Date.now.formatted(date: .omitted, time: .shortened))"
        } catch {
            status = "Offline. Open on iPhone."
        }
    }
}
