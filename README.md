# Location Lab

Location Lab is a native macOS utility for applying a test location to a connected, trusted iPhone in Developer Mode. The map-first interface supports place search, direct coordinate entry, map selection, saved favorites, device readiness checks, and GPX export.

Use Location Lab only on devices you own or are authorized to test. Location simulation can affect apps, automations, and location-based services on the connected iPhone.

## Download and install

Open the repository's **Releases** page and download one of these files:

- `Location-Lab-<version>-macOS-x86_64.dmg` — recommended installer.
- `Location-Lab-<version>-macOS-x86_64.zip` — portable application archive.
- `Location-Lab-<version>-macOS-x86_64-SHA256SUMS.txt` — checksums for verifying the downloads.

To install from the DMG:

1. Open the downloaded `.dmg` file.
2. Drag **Location Lab** into the **Applications** folder.
3. In Applications, Control-click **Location Lab** and choose **Open**.
4. Confirm **Open** when macOS warns that the developer cannot be verified.

The current bundled device runtime is built for Intel (`x86_64`) Macs. The app is not currently distributed for Windows or Linux. Apple-silicon Macs require a future arm64 dependency bundle; do not assume the Intel download will operate correctly through Rosetta.

## Requirements

- An Intel Mac running macOS 14 or newer.
- Xcode and the Xcode command-line tools installed from Apple.
- An iPhone connected by USB, unlocked, and trusted by the Mac.
- Developer Mode enabled on the iPhone.
- No companion iPhone app or separate device-support download.

Install Xcode, open it once to accept its license, and then run this command in Terminal if the command-line tools are not active:

```sh
xcode-select --install
```

## Use

1. Open **Location Lab**.
2. Connect and unlock the iPhone, then tap **Trust** if prompted.
3. On the iPhone, enable **Settings › Privacy & Security › Developer Mode**, restart, and confirm the setting if it is not already enabled.
4. Select **Check Again** in Location Lab until the device is ready.
5. Search for a place, enter `latitude, longitude`, or click the map.
6. Select **Move Here** and keep Location Lab open while testing.
7. Select **Stop and Restore Location** when finished. If the simulated location remains active, restart the iPhone to restore normal GPS behavior.

The cable can be unplugged after a session starts only when paired Wi-Fi development remains available.

## Troubleshooting

### The app will not open

Because public builds are ad-hoc signed rather than Apple-notarized, macOS may block the first launch. Control-click the app and choose **Open**. If needed, go to **System Settings › Privacy & Security** and choose **Open Anyway** for Location Lab.

### No iPhone appears

- Unlock the iPhone and reconnect its USB cable.
- Confirm the **Trust This Computer** prompt on the iPhone.
- Open Xcode and confirm the phone appears under **Window › Devices and Simulators**.
- Confirm Developer Mode is enabled on the iPhone.
- Return to Location Lab and select **Check Again**.

### The location does not return to normal

Select **Stop and Restore Location** first. If an iOS 17 or newer session persists, restart the iPhone.

## How it works

For iOS 17 and newer, the bundled provider sends coordinates through Apple's DVT location-simulation channel and maintains the session through macOS's `remotepairingd` tunnel. Older iOS versions use the `com.apple.dt.simulatelocation` developer service. Device support is bundled from the open-source [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) project.

## Build from source

Building requires macOS 14 or newer, Xcode, and its command-line tools.

```sh
swift test
VERSION=0.7.0 BUILD_NUMBER=10 ./scripts/create-dmg.sh
```

The release script creates a versioned DMG installer, ZIP archive, and checksum file in `build/releases/`. See [docs/RELEASING.md](docs/RELEASING.md) for the repository publishing workflow.

## Current limitations

- Point locations only; route playback is not exposed in the interface.
- Device readiness is derived from Xcode's device availability response.
- Public builds are not notarized unless the maintainer supplies an Apple Developer signing identity and notarization process.
- Hardware behavior must be validated with each target iPhone and iOS version.
