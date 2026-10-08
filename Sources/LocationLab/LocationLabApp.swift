import SwiftUI
import AppKit

@main
struct LocationLabApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
                .frame(minWidth: 1_040, minHeight: 680)
                .task { await model.refreshDevices() }
                .onAppear {
                    if let iconURL = Bundle.main.url(forResource: "AppIcon", withExtension: "icns"),
                       let icon = NSImage(contentsOf: iconURL) {
                        NSApplication.shared.applicationIconImage = icon
                    }
                }
        }
        .windowStyle(.titleBar)
        .commands {
            CommandGroup(after: .appInfo) {
                Button("Refresh Device Status") {
                    Task { await model.refreshDevices() }
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])
            }
        }

        Settings {
            SettingsView()
                .environmentObject(model)
                .frame(width: 520, height: 300)
        }
    }
}
