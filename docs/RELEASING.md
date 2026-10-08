# Publishing Location Lab

This repository includes a GitHub Actions workflow that builds downloadable Location Lab release files. Each release contains:

- A `.dmg` installer with an Applications shortcut.
- A `.zip` containing the executable `.app` bundle.
- A `SHA256SUMS.txt` file for download verification.

## First-time repository setup

1. Create a GitHub repository and push this complete project, including `Vendor/` and `.github/`.
2. Confirm the repository's **Actions** tab is enabled.
3. Add an open-source `LICENSE` file if you intend to permit copying or modification of your own source code. The bundled dependencies retain their own license files under `Vendor/`.
4. Update the repository description and add a screenshot if desired.

The workflow uses GitHub's automatically provided `GITHUB_TOKEN`; no extra GitHub secret is required for ad-hoc-signed builds.
It deliberately uses GitHub's `macos-15-intel` runner because the bundled device runtime contains Intel native extensions.

## Publish a release

Commit the release-ready code, then create and push a version tag:

```sh
git tag v0.7.0
git push origin v0.7.0
```

The `Release` workflow runs the tests, creates the DMG and ZIP, verifies their signatures and contents, and publishes them on the repository's **Releases** page. Use a new semantic version tag such as `v0.7.1` for each later release. Do not move or reuse a release tag after people may have downloaded it.

You can also run the workflow manually from **Actions › Release › Run workflow**. A manual run creates downloadable workflow artifacts for testing, but it does not create a public GitHub Release.

## Build release files locally

```sh
VERSION=0.7.0 BUILD_NUMBER=10 ./scripts/create-dmg.sh
```

Files are written to `build/releases/`. `VERSION` is the public semantic version and `BUILD_NUMBER` is an integer that should increase for each shipped build.

## Signing and Gatekeeper

By default, `build-release.sh` ad-hoc signs the app. Users may need to Control-click the app and select **Open** on first launch. To sign locally with an Apple Developer ID certificate, set its exact Keychain identity:

```sh
CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
VERSION=0.7.0 BUILD_NUMBER=10 ./scripts/create-dmg.sh
```

Developer ID distribution should also use hardened runtime, notarization, and stapling before public release. Those steps are intentionally not automated until the repository owner configures Apple Developer credentials and secure GitHub secrets.

## Architecture support

The checked-in Python device runtime contains Intel-only native extensions. Current release artifacts must therefore be labeled `x86_64`. Supporting Apple silicon requires rebuilding every native dependency for arm64 (or as universal binaries), testing the device tunnel on Apple silicon, and then producing a universal or separate arm64 release.
