import SwiftUI
import MapKit

struct ContentView: View {
    @EnvironmentObject private var model: AppModel
    @AppStorage("appearance.isDarkMode") private var isDarkMode = false

    var body: some View {
        Group {
            if model.deviceReady {
                MainWorkspace()
            } else {
                DeviceSetupView()
            }
        }
        .toolbar {
            ToolbarItem(placement: .navigation) {
                DeviceStatusPill()
            }
            ToolbarItem(placement: .primaryAction) {
                Button {
                    isDarkMode.toggle()
                } label: {
                    Label(
                        isDarkMode ? "Use Light Mode" : "Use Dark Mode",
                        systemImage: isDarkMode ? "sun.max.fill" : "moon.fill"
                    )
                }
                .help(isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode")
            }
        }
        .preferredColorScheme(isDarkMode ? .dark : .light)
    }
}

struct DeviceSetupView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ZStack {
            LinearGradient(colors: [Color.indigo.opacity(0.16), Color.blue.opacity(0.05)], startPoint: .topLeading, endPoint: .bottomTrailing)
                .ignoresSafeArea()
            HStack(spacing: 64) {
                VStack(spacing: 18) {
                    BrandLogoView()
                    Text("Connect your iPhone")
                        .font(.largeTitle.bold())
                    Text("Use a USB cable and enable Developer Mode. Trust is remembered after the first successful pairing.")
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: 390)
                }
                VStack(alignment: .leading, spacing: 14) {
                    Text("Device Readiness")
                        .font(.title2.bold())
                    ForEach(Array(model.readinessItems.enumerated()), id: \.offset) { _, item in
                        ReadinessRow(title: item.0, complete: item.1, help: item.2)
                    }
                    Text(model.statusMessage)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: 420, alignment: .leading)
                    HStack {
                        Button("Check Again") { Task { await model.refreshDevices() } }
                            .buttonStyle(.borderedProminent)
                        if !model.providerInstalled {
                            Button(model.providerInstalling ? "Installing…" : "Install Device Support") {
                                Task { await model.installProvider() }
                            }
                            .disabled(model.providerInstalling)
                        }
                    }
                }
                .padding(26)
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20))
                .frame(width: 470)
            }
            .padding(50)
        }
    }
}

struct BrandLogoView: View {
    private var image: NSImage? {
        guard let url = Bundle.main.url(forResource: "LocationLabLogo", withExtension: "png", subdirectory: "Brand") else {
            return nil
        }
        return NSImage(contentsOf: url)
    }

    var body: some View {
        Group {
            if let image {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFit()
            } else {
                Image(systemName: "location.circle.fill")
                    .resizable()
                    .scaledToFit()
                    .foregroundStyle(.indigo)
            }
        }
        .frame(width: 132, height: 132)
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .shadow(color: .indigo.opacity(0.22), radius: 16, y: 8)
    }
}

struct ReadinessRow: View {
    let title: String
    let complete: Bool
    let help: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: complete ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                .foregroundStyle(complete ? .green : .orange)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).fontWeight(.semibold)
                if !complete { Text(help).font(.caption).foregroundStyle(.secondary) }
            }
            Spacer()
        }
    }
}

struct MainWorkspace: View {
    @EnvironmentObject private var model: AppModel
    @State private var position: MapCameraPosition = .automatic

    var body: some View {
        NavigationSplitView {
            List(selection: $model.sidebarSelection) {
                Label("Map", systemImage: "map").tag(SidebarDestination.map)
                Label("Devices", systemImage: "iphone").tag(SidebarDestination.devices)
                Label("Favorites", systemImage: "star").tag(SidebarDestination.favorites)
                Label("Recent", systemImage: "clock").tag(SidebarDestination.recent)
                Label("GPX Files", systemImage: "point.topleft.down.to.point.bottomright.curvepath").tag(SidebarDestination.gpxFiles)
                Label("Diagnostics", systemImage: "stethoscope").tag(SidebarDestination.diagnostics)
            }
            .listStyle(.sidebar)
            .navigationSplitViewColumnWidth(min: 170, ideal: 190)
        } detail: {
            switch model.sidebarSelection {
            case .devices:
                DevicesView()
            case .favorites:
                FavoritesView()
            case .map:
                MapWorkspace(position: $position)
            case .recent:
                PlaceholderView(title: "Recent", icon: "clock", message: "Recently used locations will appear here in a future update.")
            case .gpxFiles:
                PlaceholderView(title: "GPX Files", icon: "point.topleft.down.to.point.bottomright.curvepath", message: "Export the selected map pin from Point Mode.")
            case .diagnostics:
                PlaceholderView(title: "Diagnostics", icon: "stethoscope", message: model.statusMessage)
            }
        }
        .safeAreaInset(edge: .bottom) {
            HStack {
                Circle().fill(model.deviceReady ? .green : .orange).frame(width: 8, height: 8)
                Text(model.statusMessage).lineLimit(1)
                Spacer()
                Text("Local processing").foregroundStyle(.secondary)
            }
            .font(.caption)
            .padding(.horizontal, 14)
            .frame(height: 28)
            .background(.bar)
        }
        .onAppear { model.loadCurrentLocation() }
        .onChange(of: model.selectedLocation) { _, location in
            position = .region(MKCoordinateRegion(
                center: location.coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.025, longitudeDelta: 0.025)
            ))
        }
    }
}

struct MapWorkspace: View {
    @EnvironmentObject private var model: AppModel
    @Binding var position: MapCameraPosition

    var body: some View {
        ZStack(alignment: .top) {
            MapReader { proxy in
                Map(position: $position) {
                    Marker(model.selectedLocation.name, coordinate: model.selectedLocation.coordinate)
                        .tint(.indigo)
                }
                .mapStyle(.standard(elevation: .realistic))
                .onTapGesture { point in
                    if let coordinate = proxy.convert(point, from: .local) {
                        model.select(coordinate: coordinate)
                    }
                }
            }
            HStack(alignment: .top, spacing: 14) {
                SearchCard()
                Spacer()
                DestinationCard()
            }
            .padding(18)
        }
    }
}

struct DevicesView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Devices").font(.largeTitle.bold())
                    Text("Choose which trusted iPhone receives the location.").foregroundStyle(.secondary)
                }
                Spacer()
                Button {
                    Task { await model.refreshDevices() }
                } label: {
                    Label(model.isRefreshing ? "Refreshing…" : "Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(model.isRefreshing)
            }

            if model.devices.isEmpty {
                ContentUnavailableView("No iPhone Found", systemImage: "iphone.slash", description: Text("Connect an unlocked iPhone by USB and press Refresh."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 310), spacing: 16)], spacing: 16) {
                        ForEach(model.devices) { device in
                            DeviceCard(device: device, selected: model.selectedDevice?.id == device.id)
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding(28)
    }
}

struct DeviceCard: View {
    @EnvironmentObject private var model: AppModel
    let device: AppleDevice
    let selected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "iphone.gen3")
                    .font(.system(size: 30))
                    .foregroundStyle(selected ? .white : .indigo)
                VStack(alignment: .leading) {
                    Text(device.name).font(.headline)
                    Text(device.modelName).font(.caption).foregroundStyle(selected ? .white.opacity(0.8) : .secondary)
                }
                Spacer()
                if selected { Image(systemName: "checkmark.circle.fill") }
            }
            LabeledContent("iOS", value: device.operatingSystemVersion)
            LabeledContent("Connection", value: device.interface ?? "Available")
            LabeledContent("Pairing", value: device.pairingState?.capitalized ?? "Unknown")
            Button(selected ? "Selected" : "Use This iPhone") {
                model.selectDevice(device)
            }
            .buttonStyle(.borderedProminent)
            .disabled(selected || device.pairingState != "paired")
        }
        .padding(18)
        .foregroundStyle(selected ? Color.white : Color.primary)
        .background(selected ? Color.indigo : Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(.quaternary))
    }
}

struct FavoritesView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Favorites").font(.largeTitle.bold())
                    Text("Save frequently used coordinates and reopen them on the map.").foregroundStyle(.secondary)
                }
                Spacer()
                Button {
                    model.addCurrentFavorite()
                } label: {
                    Label("Save Current Pin", systemImage: "star.fill")
                }
                .buttonStyle(.borderedProminent)
            }

            if model.favorites.isEmpty {
                ContentUnavailableView("No Favorites", systemImage: "star", description: Text("Drop a pin or search for a place, then select Save Current Pin."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(model.favorites) { favorite in
                        Button {
                            model.openFavorite(favorite)
                        } label: {
                            HStack(spacing: 14) {
                                Image(systemName: "mappin.circle.fill")
                                    .font(.title2)
                                    .foregroundStyle(.indigo)
                                VStack(alignment: .leading, spacing: 3) {
                                    Text(favorite.name).font(.headline)
                                    Text("\(favorite.latitude.formatted(.number.precision(.fractionLength(6)))), \(favorite.longitude.formatted(.number.precision(.fractionLength(6))))")
                                        .font(.caption.monospacedDigit())
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right").foregroundStyle(.tertiary)
                            }
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                    }
                    .onDelete(perform: model.removeFavorites)
                }
            }
        }
        .padding(28)
    }
}

struct PlaceholderView: View {
    let title: String
    let icon: String
    let message: String

    var body: some View {
        ContentUnavailableView(title, systemImage: icon, description: Text(message))
    }
}

struct SearchCard: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
            TextField("Search place or enter latitude, longitude", text: $model.searchText)
                .textFieldStyle(.plain)
                .onSubmit { Task { await model.search() } }
            Button("Search") { Task { await model.search() } }
                .buttonStyle(.borderless)
        }
        .padding(.horizontal, 14)
        .frame(width: 410, height: 44)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 13))
        .shadow(color: .black.opacity(0.12), radius: 10, y: 4)
    }
}

struct DestinationCard: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text("POINT MODE").font(.caption2.bold()).foregroundStyle(.indigo)
                    Text(model.selectedLocation.name).font(.title3.bold()).lineLimit(1)
                }
                Spacer()
                Button {
                    model.addCurrentFavorite()
                } label: {
                    Image(systemName: "star")
                }
                .buttonStyle(.borderless)
                .help("Add Current Pin to Favorites")
                Image(systemName: "mappin.and.ellipse").foregroundStyle(.indigo)
            }
            Divider()
            CoordinateRow(label: "Latitude", value: model.selectedLocation.latitude)
            CoordinateRow(label: "Longitude", value: model.selectedLocation.longitude)
            if let device = model.selectedDevice {
                Label("\(device.name) • Connected", systemImage: "iphone.gen3.circle.fill")
                    .font(.callout.weight(.medium))
                    .foregroundStyle(.green)
            }
            switch model.simulationState {
            case .active:
                Text("Persistent device override active. Restart the iPhone when you want to restore its real location.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Label("Restart iPhone to Restore", systemImage: "power")
                    .font(.callout.weight(.semibold))
                    .foregroundStyle(.secondary)
            case .starting:
                Button("Moving…") { }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(true)
            case .stopping:
                ProgressView().frame(maxWidth: .infinity)
            default:
                Button("Move Here") {
                    Task { await model.startSimulation() }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(!model.deviceReady || !model.providerInstalled)
            }
            Button("Export GPX…") { model.exportGPX() }
                .frame(maxWidth: .infinity)
        }
        .padding(18)
        .frame(width: 310)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.14), radius: 12, y: 5)
    }
}

struct CoordinateRow: View {
    let label: String
    let value: Double
    var body: some View {
        HStack {
            Text(label).foregroundStyle(.secondary)
            Spacer()
            Text(value.formatted(.number.precision(.fractionLength(6)))).monospacedDigit()
        }
    }
}

struct DeviceStatusPill: View {
    @EnvironmentObject private var model: AppModel
    var body: some View {
        HStack(spacing: 7) {
            Circle().fill(model.deviceReady ? .green : .orange).frame(width: 8, height: 8)
            Text(model.selectedDevice?.name ?? "No iPhone")
        }
        .font(.callout.weight(.medium))
    }
}

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    var body: some View {
        Form {
            Section("Device Support") {
                LabeledContent("Provider", value: model.providerInstalled ? "Installed" : "Not installed")
                if !model.providerInstalled {
                    Button(model.providerInstalling ? "Installing…" : "Install Device Support") {
                        Task { await model.installProvider() }
                    }
                    .disabled(model.providerInstalling)
                }
                Button("Refresh Status") { Task { await model.refreshDevices() } }
            }
            Section("Privacy") {
                Text("Location searches use MapKit. Device commands run locally on this Mac.")
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
    }
}
