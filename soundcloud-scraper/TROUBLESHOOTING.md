# SoundCloud Manager Troubleshooting

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
