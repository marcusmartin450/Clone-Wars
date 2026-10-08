import Foundation
import CoreLocation

enum SidebarDestination: String, Hashable {
    case map
    case devices
    case favorites
    case recent
    case gpxFiles
    case diagnostics
}

struct AppleDevice: Identifiable, Codable, Hashable {
    let identifier: String
    let name: String
    let modelName: String
    let operatingSystemVersion: String
    let platform: String
    let interface: String?
    let available: Bool
    let simulator: Bool
    let error: DeviceError?
    var pairingState: String?
    var developerModeStatus: String?
    var tunnelState: String?
    var ddiServicesAvailable: Bool?

    var id: String { identifier }
    var isIPhone: Bool {
        !simulator && (platform.lowercased().contains("iphoneos") || modelName.lowercased().contains("iphone"))
    }
}

struct CoreDeviceList: Decodable {
    struct Result: Decodable { let devices: [Device] }
    struct Device: Decodable {
        struct ConnectionProperties: Decodable {
            let pairingState: String?
            let tunnelState: String?
        }
        struct DeviceProperties: Decodable {
            let name: String?
            let developerModeStatus: String?
            let ddiServicesAvailable: Bool?
        }
        struct HardwareProperties: Decodable { let udid: String? }

        let connectionProperties: ConnectionProperties?
        let deviceProperties: DeviceProperties?
        let hardwareProperties: HardwareProperties?
    }
    let result: Result
}

struct DeviceError: Codable, Hashable {
    let description: String?
    let recoverySuggestion: String?
}

struct TestLocation: Identifiable, Equatable {
    let id = UUID()
    var name: String
    var latitude: Double
    var longitude: Double

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

struct FavoriteLocation: Identifiable, Codable, Equatable {
    let id: UUID
    var name: String
    var latitude: Double
    var longitude: Double

    init(id: UUID = UUID(), location: TestLocation) {
        self.id = id
        name = location.name
        latitude = location.latitude
        longitude = location.longitude
    }

    var testLocation: TestLocation {
        TestLocation(name: name, latitude: latitude, longitude: longitude)
    }
}

enum SimulationState: Equatable {
    case idle
    case starting
    case active(TestLocation)
    case stopping
    case failed(String)
}

enum CoordinateParser {
    static func parse(_ value: String) -> CLLocationCoordinate2D? {
        let parts = value.split(separator: ",", omittingEmptySubsequences: false)
        guard parts.count == 2,
              let latitude = Double(parts[0].trimmingCharacters(in: .whitespacesAndNewlines)),
              let longitude = Double(parts[1].trimmingCharacters(in: .whitespacesAndNewlines)),
              latitude.isFinite, longitude.isFinite,
              (-90...90).contains(latitude), (-180...180).contains(longitude) else {
            return nil
        }
        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

enum GPXGenerator {
    static func document(for location: TestLocation) -> String {
        let escapedName = location.name
            .replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
            .replacingOccurrences(of: ">", with: "&gt;")
            .replacingOccurrences(of: "\"", with: "&quot;")
            .replacingOccurrences(of: "'", with: "&apos;")
        return """
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="Location Lab" xmlns="http://www.topografix.com/GPX/1/1">
          <wpt lat="\(location.latitude)" lon="\(location.longitude)">
            <name>\(escapedName)</name>
          </wpt>
        </gpx>
        """
    }
}
