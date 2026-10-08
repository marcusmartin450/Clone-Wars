import Foundation
import CoreLocation

@MainActor
final class CurrentLocationService: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private let onLocation: (CLLocationCoordinate2D) -> Void
    private let onError: (String) -> Void

    init(
        onLocation: @escaping (CLLocationCoordinate2D) -> Void,
        onError: @escaping (String) -> Void
    ) {
        self.onLocation = onLocation
        self.onError = onError
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
    }

    func request() {
        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .authorized, .authorizedAlways:
            manager.requestLocation()
        case .denied, .restricted:
            onError("Allow Location Lab in System Settings › Privacy & Security › Location Services to start at your nearby current location.")
        @unknown default:
            onError("Current location is unavailable.")
        }
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        Task { @MainActor [weak self] in
            if status == .authorized || status == .authorizedAlways {
                self?.manager.requestLocation()
            }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        Task { @MainActor in
            onLocation(location.coordinate)
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor in
            onError("Could not determine the nearby current location: \(error.localizedDescription)")
        }
    }
}

struct CommandResult {
    let output: String
    let error: String
    let status: Int32
}

enum CommandRunner {
    static func run(
        executable: URL,
        arguments: [String],
        environment: [String: String] = [:]
    ) async throws -> CommandResult {
        try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            let outputPipe = Pipe()
            let errorPipe = Pipe()
            process.executableURL = executable
            process.arguments = arguments
            process.standardOutput = outputPipe
            process.standardError = errorPipe
            process.environment = ProcessInfo.processInfo.environment.merging(environment) { _, new in new }

            process.terminationHandler = { process in
                let output = String(data: outputPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                let error = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                continuation.resume(returning: CommandResult(output: output, error: error, status: process.terminationStatus))
            }

            do {
                try process.run()
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}

actor DeviceDiscoveryService {
    func discover() async throws -> [AppleDevice] {
        let result = try await CommandRunner.run(
            executable: URL(fileURLWithPath: "/usr/bin/xcrun"),
            arguments: ["xcdevice", "list", "--timeout", "3"]
        )
        guard let jsonStart = result.output.firstIndex(of: "[") else { return [] }
        let json = Data(result.output[jsonStart...].utf8)
        var devices = try JSONDecoder().decode([AppleDevice].self, from: json).filter(\.isIPhone)
        let coreDevices = await discoverCoreDevices()
        for index in devices.indices {
            guard let status = coreDevices.first(where: {
                $0.hardwareProperties?.udid == devices[index].identifier ||
                $0.deviceProperties?.name == devices[index].name
            }) else { continue }
            devices[index].pairingState = status.connectionProperties?.pairingState
            devices[index].developerModeStatus = status.deviceProperties?.developerModeStatus
            devices[index].tunnelState = status.connectionProperties?.tunnelState
            devices[index].ddiServicesAvailable = status.deviceProperties?.ddiServicesAvailable
        }
        return devices
    }

    private func discoverCoreDevices() async -> [CoreDeviceList.Device] {
        let outputURL = FileManager.default.temporaryDirectory
            .appending(path: "locationlab-devices-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: outputURL) }
        do {
            let result = try await CommandRunner.run(
                executable: URL(fileURLWithPath: "/usr/bin/xcrun"),
                arguments: ["devicectl", "--timeout", "8", "--json-output", outputURL.path, "list", "devices"]
            )
            guard result.status == 0,
                  let data = try? Data(contentsOf: outputURL),
                  let response = try? JSONDecoder().decode(CoreDeviceList.self, from: data) else {
                return []
            }
            return response.result.devices
        } catch {
            return []
        }
    }
}

enum ProviderError: LocalizedError {
    case notInstalled
    case commandFailed(String)

    var errorDescription: String? {
        switch self {
        case .notInstalled:
            "Device support is not installed. Select Install Device Support first."
        case .commandFailed(let message):
            message.isEmpty ? "The device-location command failed." : message
        }
    }
}

actor MobileDeviceProvider {
    private let fileManager = FileManager.default
    private var activeProcess: Process?
    private var activeErrorPipe: Pipe?

    private var bundledModulesURL: URL? {
        guard let url = Bundle.main.resourceURL?.appending(path: "python"),
              fileManager.fileExists(atPath: url.appending(path: "pymobiledevice3").path) else {
            return nil
        }
        return url
    }

    var executableURL: URL? {
        let home = fileManager.homeDirectoryForCurrentUser
        let candidates = [
            home.appending(path: "Library/Application Support/LocationLab/provider/bin/pymobiledevice3"),
            URL(fileURLWithPath: "/opt/homebrew/bin/pymobiledevice3"),
            URL(fileURLWithPath: "/usr/local/bin/pymobiledevice3")
        ]
        return candidates.first { fileManager.isExecutableFile(atPath: $0.path) }
    }

    func isInstalled() -> Bool { bundledModulesURL != nil || executableURL != nil }

    func sessionIsRunning() -> Bool {
        activeProcess?.isRunning == true
    }

    func install() async throws {
        let providerDirectory = fileManager.homeDirectoryForCurrentUser
            .appending(path: "Library/Application Support/LocationLab/provider")
        try fileManager.createDirectory(at: providerDirectory.deletingLastPathComponent(), withIntermediateDirectories: true)

        let pythonCandidates = [
            "/usr/bin/python3",
            "/Applications/Xcode.app/Contents/Developer/usr/bin/python3"
        ]
        guard let python = pythonCandidates.first(where: { fileManager.isExecutableFile(atPath: $0) }) else {
            throw ProviderError.commandFailed("Python 3 is unavailable. Install the Xcode command-line tools.")
        }

        let venv = try await CommandRunner.run(
            executable: URL(fileURLWithPath: python),
            arguments: ["-m", "venv", providerDirectory.path]
        )
        guard venv.status == 0 else { throw ProviderError.commandFailed(venv.error) }

        let pip = providerDirectory.appending(path: "bin/pip")
        let install = try await CommandRunner.run(
            executable: pip,
            arguments: ["install", "--upgrade", "pymobiledevice3"]
        )
        guard install.status == 0 else { throw ProviderError.commandFailed(install.error) }
    }

    func set(_ location: TestLocation, osVersion: String, deviceID: String) async throws {
        guard isInstalled() else { throw ProviderError.notInstalled }
        let executableURL = executableURL ?? URL(fileURLWithPath: "/usr/bin/python3")
        let major = Int(osVersion.prefix { $0.isNumber }) ?? 17
        let arguments: [String]
        if major >= 17 {
            arguments = ["developer", "dvt", "simulate-location", "set", "--", String(location.latitude), String(location.longitude)]
        } else {
            arguments = ["developer", "simulate-location", "set", String(location.latitude), String(location.longitude)]
        }
        if major >= 17 {
            try await startHeldSession(executableURL, arguments: arguments, deviceID: deviceID)
        } else {
            try await execute(executableURL, arguments: arguments, deviceID: deviceID)
        }
    }

    func clear(osVersion: String, deviceID: String) async throws {
        guard isInstalled() else { throw ProviderError.notInstalled }
        let executableURL = executableURL ?? URL(fileURLWithPath: "/usr/bin/python3")
        stopHeldSession()
        let major = Int(osVersion.prefix { $0.isNumber }) ?? 17
        let arguments = major >= 17
            ? ["developer", "dvt", "simulate-location", "clear"]
            : ["developer", "simulate-location", "clear"]
        try await execute(executableURL, arguments: arguments, deviceID: deviceID)
    }

    private func startHeldSession(_ executable: URL, arguments: [String], deviceID: String) async throws {
        stopHeldSession()
        let launch = launchConfiguration(executable: executable, arguments: arguments, deviceID: deviceID)
        let process = Process()
        let errorPipe = Pipe()
        process.executableURL = launch.executable
        process.arguments = launch.arguments
        process.environment = ProcessInfo.processInfo.environment.merging(launch.environment) { _, new in new }
        process.standardOutput = FileHandle.nullDevice
        process.standardError = errorPipe
        process.standardInput = FileHandle.nullDevice
        try process.run()

        activeProcess = process
        activeErrorPipe = errorPipe
        try await Task.sleep(for: .seconds(3))

        guard process.isRunning else {
            let error = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            activeProcess = nil
            activeErrorPipe = nil
            throw ProviderError.commandFailed(error)
        }
    }

    private func stopHeldSession() {
        guard let process = activeProcess else { return }
        if process.isRunning { process.terminate() }
        process.waitUntilExit()
        activeProcess = nil
        activeErrorPipe = nil
    }

    private func execute(_ executable: URL, arguments: [String], deviceID: String) async throws {
        let launch = launchConfiguration(executable: executable, arguments: arguments, deviceID: deviceID)
        let result = try await CommandRunner.run(
            executable: launch.executable,
            arguments: launch.arguments,
            environment: launch.environment
        )
        guard result.status == 0 else {
            throw ProviderError.commandFailed(result.error.isEmpty ? result.output : result.error)
        }
    }

    private func launchConfiguration(
        executable: URL,
        arguments: [String],
        deviceID: String
    ) -> (executable: URL, arguments: [String], environment: [String: String]) {
        var command = executable
        var commandArguments = arguments
        var environment = [
            "PYMOBILEDEVICE3_NATIVE": "1",
            "PYMOBILEDEVICE3_DEFAULT_FALLBACK": "native",
            "PYMOBILEDEVICE3_UDID": deviceID,
            "NO_COLOR": "1",
            "PYTHONUNBUFFERED": "1"
        ]
        if let bundledModulesURL {
            command = URL(fileURLWithPath: "/usr/bin/python3")
            commandArguments = ["-m", "pymobiledevice3"] + arguments
            environment["PYTHONPATH"] = bundledModulesURL.path
        }
        return (command, commandArguments, environment)
    }
}
