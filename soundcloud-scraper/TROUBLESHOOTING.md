# SoundCloud Manager Troubleshooting

## Apple Could Not Verify the Installer

This warning appears because `Install SoundCloud Manager.command` is not currently signed and notarized with a paid Apple Developer certificate. It does not mean the installer has already failed.

Only override the warning when the ZIP came from this repository and you trust the files.

1. Try to open `Install SoundCloud Manager.command` once.
2. Click `Done` on the warning.
3. Open `System Settings` from the Apple menu.
4. Select `Privacy & Security` and scroll to `Security`.
5. Find the blocked installer message and click `Open Anyway`.
6. Enter the Mac login password.
7. Click `Open` when macOS asks for confirmation.

Apple normally shows `Open Anyway` for about one hour after the blocked attempt. Follow [Apple's official unnotarized-app instructions](https://support.apple.com/en-au/102445) if the wording is different on your macOS version.

If `Open Anyway` is missing:

- Try opening the installer again, then immediately return to `Privacy & Security`.
- Confirm you are using an administrator account or can enter an administrator password.
- Re-download the ZIP if it may be incomplete or damaged.
- Do not disable Gatekeeper for the entire Mac.

The first launch of `SoundCloud Manager.app` may show the same warning. Repeat the steps for the app. A warning-free public release would require Apple Developer signing and Apple notarization.

## SoundCloud Says the Track Is DRM Protected

- This can appear as `ERROR: [soundcloud] <track id>: This video is DRM protected`.
- The application should still display the track using information from its URL.
- Click `Download Track` normally.
- The pinned nightly `yt-dlp` build tries SoundCloud first.
- If that attempt fails, the progress panel should say `Searching YouTube for an alternative source`.
- A successful fallback ends with `Download complete using YouTube fallback`.

## The YouTube Fallback Finds the Wrong Version

- The search uses the artist and title collected from SoundCloud.
- YouTube may rank a remix, radio edit, live recording, or unofficial upload first.
- Check the finished MP3 before moving it into a permanent music library.
- If the wrong result is selected, search YouTube manually and download the correct URL with the terminal helper.

## The Download Fails on Both Services

- Confirm that the Mac is online.
- Run the installer again to restore the pinned packages.
- Make sure FFmpeg is available:

```bash
ffmpeg -version
```

- Confirm the packaged `yt-dlp` version:

```bash
.venv/bin/python -m yt_dlp --version
```

- The expected tested version is `2026.09.27.232945` from the nightly package `2026.9.27.232945.dev0`.
- Private, removed, age-restricted, region-restricted, or unavailable media may have no usable source.

## Brave Browser Is Not Found

- Install Brave in `/Applications` or your user Applications folder.
- Run `Install SoundCloud Manager.command` again.
- Brave is needed for private-browser scraping and playlist loading, but not for every direct track download.

## The Application Does Not Open

- Right-click `SoundCloud Manager.app` and choose `Open`.
- If setup has not completed, double-click `Install SoundCloud Manager.command`.
- For diagnostic output, run:

```bash
cd soundcloud-scraper
.venv/bin/python soundcloud_easy_start.py
```

## Downloads Go to the Wrong Folder

- Click `Choose Download Folder` in the GUI before starting downloads.
- GUI downloads use the selected folder.
- The separate `scdl` terminal helper always uses `/Users/nickswatts/Music/usb` unless its script is edited.

## The Download Totals Look Stuck

- Current versions update downloaded, skipped, and failed totals after every track.
- The `Processed X of Y` message shows playlist progress while the job is still running.
- Older packages only updated the top-level totals when the full job ended; reinstall from the latest ZIP if that behavior remains.

## Excel Is Not Created

- Use a profile or Likes URL rather than a single track URL.
- Set the requested number of tracks from 1 to 100.
- Choose the scrape-and-Excel option and keep Brave open while the page loads.
- Do not delete the main profile CSV if you want later runs to continue from saved progress.

## Run the Focused Tests

```bash
.venv/bin/python -m unittest -v test_easy_gui.py test_soundcloud_exact_downloader.py
```

The tests do not download a full song. They verify URL classification, fallback query construction, SoundCloud-first ordering, and successful handling of a mocked YouTube fallback.
