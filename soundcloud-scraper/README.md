# SoundCloud Manager for Mac

- SoundCloud Manager provides one simple GUI for tracks, playlists, profiles, and Likes pages.
- It creates organized CSV and Excel files and can download selected tracks as MP3 files.
- New users do not need to run Terminal commands after the one-time installation.

## Download the App

- Download [`dist/SoundCloud-Manager-Mac.zip`](dist/SoundCloud-Manager-Mac.zip).
- Unzip it on a Mac.
- Double-click `Install SoundCloud Manager.command` one time.
- After setup finishes, double-click `SoundCloud Manager.app` whenever you want to use it.
- If macOS blocks either file, right-click it, choose `Open`, and confirm `Open` again.

## What the Installer Does

- Creates a private Python environment inside the application folder.
- Installs the pinned dependencies from `requirements.txt`.
- Uses the tested nightly `yt-dlp` build instead of the standard release.
- Checks for Python 3, Brave Browser, and FFmpeg.
- Uses Homebrew to install missing system packages when Homebrew is available.
- Opens the official download page when a required application must be installed manually.

## Use the GUI

- Paste a SoundCloud track, playlist, profile, or Likes URL.
- Set the Likes limit from 1 to 100 when using a profile or Likes page.
- Click `Use This URL`.
- Use `Choose Download Folder` before downloading if you want a different destination.
- Track and playlist downloads run in the background so the GUI stays responsive.
- The progress panel displays live status and final downloaded, skipped, and failed counts.

## Track Downloads

- The application always tries the original SoundCloud URL first with its pinned nightly `yt-dlp` installation.
- If SoundCloud reports an unavailable stream, HTTP error, or DRM-protected track, the application searches YouTube using the scraped artist and title.
- The first matching YouTube result is downloaded only after the SoundCloud attempt fails.
- The GUI reports `Download complete using YouTube fallback` when the alternate source succeeds.
- MP3 quality is set to `0`, artwork is converted to JPG and embedded, track metadata is added, and the genre is set to House.
- Downloads are saved in the folder selected in the GUI.

The fallback was verified with `Mellizos & Mixmasters - My Life Is A Disco (In The Mix)` after SoundCloud track `2314350962` returned a DRM error.

## Playlist Downloads

- Playlist pages are opened through Brave Private Browsing.
- The GUI displays the tracks before downloading.
- Select the tracks you want and click `Download Selected`.
- Playlist order is preserved and existing downloads can be skipped.

## Profile and Likes Pages

- The scraper opens the page through Brave Private Browsing.
- It collects the requested number of tracks and preserves previously collected rows.
- It creates CSV and Excel files and displays the scraped tracks in the GUI.
- Select tracks and click `Download Selected Songs` to download them in the background.

## Excel Workbook

- `All Tracks Cleaned` contains the cleaned track list.
- `Genre Mapping` explains how genres were organized.
- `Artist Index` sorts tracks by artist and title and includes clickable SoundCloud, download, and buy links.
- `USB Download List` is ready for selected tracks.
- Every organized genre receives its own alphabetically arranged worksheet.

## Terminal Helper

- `scdl.sh` keeps the terminal helper available for advanced users.
- Its default download destination remains `/Users/nickswatts/Music/usb`.
- The GUI destination setting does not change the terminal helper destination.

## Requirements

- macOS
- Python 3
- Brave Browser
- FFmpeg
- Internet access during installation, scraping, and downloading

Pinned Python packages:

```text
openpyxl==3.1.5
playwright==1.58.0
yt-dlp[default]==2026.9.27.232945.dev0
```

## Run from Source

```bash
cd soundcloud-scraper
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python soundcloud_easy_start.py
```

## Tests

```bash
.venv/bin/python -m unittest -v test_easy_gui.py test_soundcloud_exact_downloader.py
```

- The fallback tests confirm that nightly `yt-dlp` attempts SoundCloud first and only then uses a YouTube search.
- The packaged application was compiled and tested from a clean ZIP extraction.
- See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for common errors and recovery steps.

## Important Notes

- Only download audio you have permission to download.
- A YouTube search can return a different edit, remix, or upload; verify the finished track before using it.
- Private, removed, region-restricted, or unavailable tracks can still fail on both services.
- The package does not include passwords, browser cookies, account credentials, downloaded music, or personal scrape data.
- Do not delete the main profile CSV if you want scraper progress to be preserved.

## Main Files

- `SoundCloud Manager.app` starts the GUI.
- `Install SoundCloud Manager.command` performs the one-time installation.
- `soundcloud_easy_gui.py` provides the one-URL interface and background progress display.
- `soundcloud_easy_start.py` enables the integrated application features.
- `soundcloud_exact_downloader.py` performs nightly-first SoundCloud downloading and YouTube fallback.
- `soundcloud_download_jobs.py` manages background downloads and result counts.
- `soundcloud_artist_extension.py` creates the Artist Index worksheet.
- `soundcloud_playlist_browser.py` loads playlists through Brave.
- `soundcloud_scraper_backend.py` collects profile and Likes tracks.
- `sc_likes_scraper4_organized_outputs.py` creates the CSV and Excel outputs.
