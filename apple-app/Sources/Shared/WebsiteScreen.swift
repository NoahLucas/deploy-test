#if os(iOS) || os(visionOS)
import SwiftUI

struct WebsiteScreen: View {
    @State private var reloadID = UUID()
    @State private var isLoading = true
    @State private var errorMessage: String?

    private var showError: Binding<Bool> {
        Binding(
            get: { errorMessage != nil },
            set: { shouldShow in
                if !shouldShow {
                    errorMessage = nil
                }
            }
        )
    }

    var body: some View {
        ZStack(alignment: .top) {
            WebsiteWebView(
                url: SiteConfiguration.websiteURL,
                reloadID: reloadID,
                isLoading: $isLoading,
                errorMessage: $errorMessage
            )
            .ignoresSafeArea(edges: .bottom)

            if isLoading {
                ProgressView("Loading noahlucas.com...")
                    .padding(12)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 10))
                    .padding(.top, 10)
            }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    reloadID = UUID()
                } label: {
                    Label("Reload", systemImage: "arrow.clockwise")
                }
            }

            ToolbarItem(placement: .topBarTrailing) {
                ShareLink(item: SiteConfiguration.websiteURL) {
                    Label("Share", systemImage: "square.and.arrow.up")
                }
            }
        }
        .alert(
            "Could Not Load noahlucas.com",
            isPresented: showError,
            actions: {
                Button("Retry") {
                    reloadID = UUID()
                }

                Button("Dismiss", role: .cancel) {
                    errorMessage = nil
                }
            },
            message: {
                Text(errorMessage ?? "Please check your internet connection and try again.")
            }
        )
    }
}
#endif
