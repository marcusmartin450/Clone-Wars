import AppKit
import Foundation
@preconcurrency import MapKit

@MainActor
final class AppModel: ObservableObject {
    @Published var devices: [AppleDevice] = []
    @Published var selectedDeviceID: String?
    @Published var isRefreshing = false
    @Published var providerInstalled = false
    @Published var providerInstalling = false
    @Published var statusMessage = "Connect your iPhone to begin."
    @Published var searchText = ""
    @Published var selectedLocation = TestLocation(name: "Apple Park", latitude: 37.3349, longitude: -122.0090)
    @Published var simulationState: SimulationState = .idle
    @Published var sidebarSelection: SidebarDestination = .map
    @Published private(set) var favorites: [FavoriteLocation]

    private let discovery = DeviceDiscoveryService()
    private let provider = MobileDeviceProvider()
    private var hasUserSelectedLocation = false
    private var sessionMonitor: Task<Void, Never>?
    private let favoritesKey = "locationLab.favorites"
    private lazy var currentLocationService = CurrentLocationService(
        onLocation: { [weak self] coordinate in
            guard let self, !self.hasUserSelectedLocation else { return }
            self.selectedLocation = TestLocation(
                name: "Current Nearby Location",
                latitude: coordinate.latitude,
                longitude: coordinate.longitude
            )
            self.statusMessage = "Map centered on this Mac’s current location beside the connected iPhone."
        },
        onError: { [weak self] message in
            self?.statusMessage = message
        }
    )

    init() {
        if let data = UserDefaults.standard.data(forKey: favoritesKey),
           let saved = try? JSONDecoder().decode([FavoriteLocation].self, from: data) {
            favorites = saved
        } else {
            favorites = []
        }
    }

    var selectedDevice: AppleDevice? {
        devices.first { $0.identifier == selectedDeviceID } ?? devices.first
    }

    var deviceReady: Bool {
        guard let device = selectedDevice else { return false }
        return device.pairingState == "paired" &&
            providerInstalled
    }

    var readinessItems: [(String, Bool, String)] {
        let device = selectedDevice
        let connected = device != nil
        let paired = device?.pairingState == "paired"
        return [
            ("Xcode Installed", FileManager.default.fileExists(atPath: "/Applications/Xcode.app"), "Install Xcode from Apple."),
            ("iPhone Connected", connected, "Connect by USB, or enable paired network development before unplugging."),
            ("Computer Trusted", paired, "Unlock the iPhone and tap Trust only if a new prompt appears."),
            ("Device Paired", paired, "Complete pairing in Xcode if prompted."),
            ("Developer Mode", device?.developerModeStatus == "enabled", "If Developer Mode is already on, continue; the location provider verifies it when starting."),
            ("Device Support", providerInstalled, "Install the local device-support provider.")
        ]
    }

    func refreshDevices() async {
        isRefreshing = true
        providerInstalled = await provider.isInstalled()
        do {
            devices = try await discovery.discover()
            if selectedDeviceID == nil { selectedDeviceID = devices.first?.identifier }
            if devices.isEmpty {
                statusMessage = "No iPhone found. Connect one with a USB cable."
            } else if selectedDevice?.pairingState == "paired" && selectedDevice?.developerModeStatus == "disabled" {
                statusMessage = "Connected and paired. Developer Mode will be verified when the test location starts."
            } else if selectedDevice?.pairingState != "paired" {
                statusMessage = "Unlock the iPhone and approve Trust only if prompted."
            } else if !providerInstalled {
                statusMessage = "Device connection is ready. Install Device Support to continue."
            } else {
                statusMessage = deviceReady ? "Device ready." : selectedDevice?.error?.recoverySuggestion ?? "Unlock the iPhone and check Developer Mode."
            }
        } catch {
            statusMessage = "Device check failed: \(error.localizedDescription)"
        }
        isRefreshing = false
    }

    func installProvider() async {
        providerInstalling = true
        statusMessage = "Installing device support…"
        do {
            try await provider.install()
            providerInstalled = true
            statusMessage = "Device support installed."
        } catch {
            statusMessage = "Installation failed: \(error.localizedDescription)"
        }
        providerInstalling = false
    }

    func search() async {
        if let coordinate = CoordinateParser.parse(searchText) {
            hasUserSelectedLocation = true
            selectedLocation = TestLocation(name: "Custom Coordinate", latitude: coordinate.latitude, longitude: coordinate.longitude)
            return
        }
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = searchText
        do {
            let response = try await MKLocalSearch(request: request).start()
            if let item = response.mapItems.first {
                hasUserSelectedLocation = true
                selectedLocation = TestLocation(
                    name: item.name ?? searchText,
                    latitude: item.placemark.coordinate.latitude,
                    longitude: item.placemark.coordinate.longitude
                )
            } else {
                statusMessage = "No matching location found."
            }
        } catch {
            statusMessage = "Search failed: \(error.localizedDescription)"
        }
    }

    func select(coordinate: CLLocationCoordinate2D) {
        hasUserSelectedLocation = true
        selectedLocation = TestLocation(name: "Dropped Pin", latitude: coordinate.latitude, longitude: coordinate.longitude)
    }

    func selectDevice(_ device: AppleDevice) {
        selectedDeviceID = device.identifier
        statusMessage = "Using \(device.name)."
        sidebarSelection = .map
    }

    func addCurrentFavorite() {
        let alreadySaved = favorites.contains {
            abs($0.latitude - selectedLocation.latitude) < 0.0000001 &&
                abs($0.longitude - selectedLocation.longitude) < 0.0000001
        }
        guard !alreadySaved else {
            statusMessage = "This location is already in Favorites."
            return
        }
        favorites.append(FavoriteLocation(location: selectedLocation))
        saveFavorites()
        statusMessage = "Added \(selectedLocation.name) to Favorites."
    }

    func openFavorite(_ favorite: FavoriteLocation) {
        hasUserSelectedLocation = true
        selectedLocation = favorite.testLocation
        sidebarSelection = .map
        statusMessage = "Opened \(favorite.name) from Favorites."
    }

    func removeFavorites(at offsets: IndexSet) {
        for index in offsets.sorted(by: >) {
            favorites.remove(at: index)
        }
        saveFavorites()
    }

    private func saveFavorites() {
        guard let data = try? JSONEncoder().encode(favorites) else { return }
        UserDefaults.standard.set(data, forKey: favoritesKey)
    }

    func loadCurrentLocation() {
        currentLocationService.request()
    }

    func startSimulation() async {
        guard let device = selectedDevice,
              device.pairingState == "paired" else {
            statusMessage = "Connect, unlock, and trust an iPhone first."
            return
        }
        simulationState = .starting
        sessionMonitor?.cancel()
        do {
            try await provider.set(selectedLocation, osVersion: device.operatingSystemVersion, deviceID: device.identifier)
            simulationState = .active(selectedLocation)
            statusMessage = "Persistent location packet accepted by \(device.name). Restart the iPhone to restore real GPS."
            monitorSession(location: selectedLocation, device: device)
        } catch {
            simulationState = .failed(error.localizedDescription)
            statusMessage = error.localizedDescription
        }
    }

    func stopSimulation() async {
        guard let device = selectedDevice else { return }
        sessionMonitor?.cancel()
        sessionMonitor = nil
        simulationState = .stopping
        do {
            try await provider.clear(osVersion: device.operatingSystemVersion, deviceID: device.identifier)
            simulationState = .idle
            statusMessage = "Location simulation stopped."
        } catch {
            simulationState = .failed(error.localizedDescription)
            statusMessage = error.localizedDescription
        }
    }

    private func monitorSession(location: TestLocation, device: AppleDevice) {
        sessionMonitor = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(2))
                guard !Task.isCancelled else { return }
                if await provider.sessionIsRunning() { continue }

                statusMessage = "USB connection changed. Reconnecting through paired Wi-Fi…"
                var lastError = "The native device tunnel disconnected."
                for _ in 0..<5 {
                    guard !Task.isCancelled else { return }
                    do {
                        try await provider.set(location, osVersion: device.operatingSystemVersion, deviceID: device.identifier)
                        simulationState = .active(location)
                        statusMessage = "Persistent location packet restored through paired Wi-Fi on \(device.name)."
                        lastError = ""
                        break
                    } catch {
                        lastError = error.localizedDescription
                        try? await Task.sleep(for: .seconds(2))
                    }
                }
                if !lastError.isEmpty {
                    simulationState = .failed(lastError)
                    statusMessage = "Wi-Fi handoff failed: \(lastError)"
                    return
                }
            }
        }
    }

    func exportGPX() {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.xml]
        panel.nameFieldStringValue = "LocationLab.gpx"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        do {
            try GPXGenerator.document(for: selectedLocation).write(to: url, atomically: true, encoding: .utf8)
            statusMessage = "GPX exported to \(url.lastPathComponent)."
        } catch {
            statusMessage = "Export failed: \(error.localizedDescription)"
        }
    }
}
