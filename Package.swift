// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "LocationLab",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "LocationLab", targets: ["LocationLab"])
    ],
    targets: [
        .executableTarget(
            name: "LocationLab",
            path: "Sources/LocationLab"
        ),
        .testTarget(
            name: "LocationLabTests",
            dependencies: ["LocationLab"],
            path: "Tests/LocationLabTests"
        )
    ]
)
