import SwiftUI

struct IOSRootView: View {
    var body: some View {
        TabView {
            NavigationStack {
                WebsiteScreen()
                    .navigationTitle("Noah Lucas")
                    .navigationBarTitleDisplayMode(.inline)
            }
            .tabItem {
                Label("Site", systemImage: "globe")
            }

            NavigationStack {
                ControlCenterView()
            }
            .tabItem {
                Label("Control", systemImage: "slider.horizontal.3")
            }
        }
    }
}
