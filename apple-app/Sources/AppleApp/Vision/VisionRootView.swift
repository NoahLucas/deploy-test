import SwiftUI

struct VisionRootView: View {
    var body: some View {
        NavigationStack {
            WebsiteScreen()
                .navigationTitle("Noah Lucas")
                .navigationBarTitleDisplayMode(.inline)
        }
    }
}
