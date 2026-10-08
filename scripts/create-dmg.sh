#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
BUILD_DIR="$ROOT_DIR/build"
DMG_DIR="$BUILD_DIR/dmg"
RELEASE_DIR="$BUILD_DIR/releases"

"$ROOT_DIR/scripts/build-release.sh"
APP_DIR="$BUILD_DIR/Location Lab.app"
VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_DIR/Contents/Info.plist")"
ARCHITECTURES="$(lipo -archs "$APP_DIR/Contents/MacOS/LocationLab" | tr ' ' '-')"
BASE_NAME="Location-Lab-$VERSION-macOS-$ARCHITECTURES"
DMG_PATH="$RELEASE_DIR/$BASE_NAME.dmg"
ZIP_PATH="$RELEASE_DIR/$BASE_NAME.zip"

rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"
mkdir -p "$RELEASE_DIR"
cp -R "$APP_DIR" "$DMG_DIR/"
ln -sfn /Applications "$DMG_DIR/Applications"
hdiutil create -volname "Location Lab" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_DIR" "$ZIP_PATH"

(
  cd "$RELEASE_DIR"
  shasum -a 256 "$BASE_NAME.dmg" "$BASE_NAME.zip" > "$BASE_NAME-SHA256SUMS.txt"
)

echo "$RELEASE_DIR"
