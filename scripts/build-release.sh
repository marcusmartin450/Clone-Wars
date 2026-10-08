#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
BUILD_DIR="$ROOT_DIR/build"
APP_DIR="$BUILD_DIR/Location Lab.app"
CONTENTS_DIR="$APP_DIR/Contents"
VERSION="${VERSION:-0.7.0}"
BUILD_NUMBER="${BUILD_NUMBER:-10}"
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:--}"

if [[ ! "$VERSION" =~ '^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$' ]]; then
  echo "VERSION must look like 1.2.3 or 1.2.3-beta.1" >&2
  exit 1
fi

if [[ ! "$BUILD_NUMBER" =~ '^[0-9]+$' ]]; then
  echo "BUILD_NUMBER must be an integer" >&2
  exit 1
fi

cd "$ROOT_DIR"
mkdir -p .build/cache .build/config .build/security .build/clang-module-cache
CLANG_MODULE_CACHE_PATH="$ROOT_DIR/.build/clang-module-cache" swift build \
  -c release \
  --disable-sandbox \
  --cache-path .build/cache \
  --config-path .build/config \
  --security-path .build/security

rm -rf "$APP_DIR"
mkdir -p "$CONTENTS_DIR/MacOS" "$CONTENTS_DIR/Resources"
cp ".build/release/LocationLab" "$CONTENTS_DIR/MacOS/LocationLab"
cp "$ROOT_DIR/README.md" "$CONTENTS_DIR/Resources/README.md"
ditto "$ROOT_DIR/Vendor/pymobiledevice3" "$CONTENTS_DIR/Resources/python"
ditto "$ROOT_DIR/Assets/Brand" "$CONTENTS_DIR/Resources/Brand"
xcrun actool \
  --compile "$CONTENTS_DIR/Resources" \
  --platform macosx \
  --minimum-deployment-target 14.0 \
  --app-icon AppIcon \
  --output-partial-info-plist "$BUILD_DIR/AppIcon-partial.plist" \
  "$ROOT_DIR/Assets/LocationLab.xcassets" >/dev/null

cat > "$CONTENTS_DIR/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>LocationLab</string>
  <key>CFBundleIdentifier</key><string>com.locationlab.mac</string>
  <key>CFBundleName</key><string>Location Lab</string>
  <key>CFBundleDisplayName</key><string>Location Lab</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundleIconName</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$BUILD_NUMBER</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.developer-tools</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSLocationWhenInUseUsageDescription</key><string>Location Lab uses this Mac's current location to center the map near the connected iPhone.</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST

codesign --force --deep --sign "$CODESIGN_IDENTITY" "$APP_DIR"
echo "$APP_DIR"
