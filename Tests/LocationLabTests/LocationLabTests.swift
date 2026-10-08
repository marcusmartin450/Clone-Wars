import XCTest
@testable import LocationLab

final class LocationLabTests: XCTestCase {
    func testCoordinateParsing() {
        let coordinate = CoordinateParser.parse(" 40.7128, -74.0060 ")
        XCTAssertEqual(coordinate?.latitude, 40.7128)
        XCTAssertEqual(coordinate?.longitude, -74.0060)
    }

    func testCoordinateBounds() {
        XCTAssertNil(CoordinateParser.parse("91, 0"))
        XCTAssertNil(CoordinateParser.parse("0, -181"))
        XCTAssertNil(CoordinateParser.parse("nan, 0"))
    }

    func testGPXEscaping() {
        let location = TestLocation(name: "A&B <Place>", latitude: 1, longitude: 2)
        let document = GPXGenerator.document(for: location)
        XCTAssertTrue(document.contains("A&amp;B &lt;Place&gt;"))
    }

    func testCoreDeviceReadinessDecoding() throws {
        let data = Data(#"{"result":{"devices":[{"connectionProperties":{"pairingState":"paired","tunnelState":"unavailable"},"deviceProperties":{"name":"Marcus’s iPhone","developerModeStatus":"disabled","ddiServicesAvailable":false},"hardwareProperties":{"udid":"00008130"}}]}}"#.utf8)
        let device = try JSONDecoder().decode(CoreDeviceList.self, from: data).result.devices[0]
        XCTAssertEqual(device.connectionProperties?.pairingState, "paired")
        XCTAssertEqual(device.deviceProperties?.developerModeStatus, "disabled")
    }

    func testFavoriteLocationRoundTrip() throws {
        let favorite = FavoriteLocation(location: TestLocation(name: "Home", latitude: 26.1, longitude: -80.2))
        let data = try JSONEncoder().encode([favorite])
        let decoded = try JSONDecoder().decode([FavoriteLocation].self, from: data)
        XCTAssertEqual(decoded, [favorite])
        XCTAssertEqual(decoded[0].testLocation.name, "Home")
    }
}
