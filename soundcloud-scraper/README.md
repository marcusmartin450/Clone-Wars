# SoundCloud Manager for Mac

- SoundCloud Manager provides one simple GUI for tracks, playlists, profiles, and Likes pages.
- It creates organized CSV and Excel files and can download selected tracks as MP3 files.
- New users do not need to run Terminal commands after the one-time installation.

> **Brave Browser is required for playlists, profiles, Likes pages, and creating new scraped Excel workbooks.** Install Brave before setting up SoundCloud Manager: [Download Brave from the official website](https://brave.com/download/).

Before installing, read the complete [`REQUIREMENTS.md`](REQUIREMENTS.md) page.

## Download the App

- Download [`dist/SoundCloud-Manager-Mac.zip`](dist/SoundCloud-Manager-Mac.zip).
- Unzip it on a Mac.
- Double-click `Install SoundCloud Manager.command` one time.
- After setup finishes, double-click `SoundCloud Manager.app` whenever you want to use it.
- If macOS blocks either file, right-click it, choose `Open`, and confirm `Open` again.

## Beginner Tutorial

You do not need to know how to program or use Terminal. Follow these steps in order.

### 1. Download and Unzip

1. Click [`SoundCloud-Manager-Mac.zip`](dist/SoundCloud-Manager-Mac.zip).
2. Open your Mac's `Downloads` folder in Finder.
3. Double-click the ZIP file if your Mac did not unzip it automatically.
4. Open the new `SoundCloud Manager` folder.
5. Keep everything inside this folder together. Do not move only the `.app` file somewhere else.

### 2. Install It One Time

1. First install [Brave Browser](https://brave.com/download/). Playlist, profile, Likes, and scraper features will not work without it.
2. Open Brave at least once, then close it.
3. Double-click `Install SoundCloud Manager.command`.
4. If macOS blocks it, right-click the file, choose `Open`, and click `Open` again.
5. Follow each message that appears.
6. Keep the setup window open until it says setup is finished.
7. Setup may take several minutes because it checks and installs the required software.
8. You do not need to run the installer again unless setup failed or you are repairing the application.

### If Apple Says It Cannot Verify the Installer

SoundCloud Manager is not currently signed and notarized with a paid Apple Developer certificate. macOS may display `Apple could not verify` or say the developer cannot be verified.

Only continue if you downloaded the ZIP from this repository and trust the files.

1. Try to open `Install SoundCloud Manager.command` once.
2. Click `Done` when macOS blocks it.
3. Open the Apple menu and choose `System Settings`.
4. Select `Privacy & Security`.
5. Scroll down to the `Security` section.
6. Find the message about `Install SoundCloud Manager.command`.
7. Click `Open Anyway`.
8. Enter the Mac login password when asked.
9. Click `Open` to start the installer.

The `Open Anyway` button is normally available for about one hour after the blocked attempt. See [Apple's instructions for opening an unnotarized app](https://support.apple.com/en-au/102445).

The same steps may be needed the first time `SoundCloud Manager.app` is opened. After macOS saves the exception, the file should open normally in the future.

### 3. Open SoundCloud Manager

1. Double-click `SoundCloud Manager.app`.
2. Your web browser will open the SoundCloud Manager screen.
3. The application runs privately on your Mac. The local browser address is normal.
4. If the installer opens instead, allow it to finish and then open the app again.

### 4. Choose Where Music Is Saved

1. Click `Choose Download Folder`.
2. Select a folder such as `Downloads`, `Music`, or a USB drive.
3. Confirm the folder.
4. All downloads started from the GUI will use this folder until you choose another one.

### 5. Copy a SoundCloud Link

1. Open SoundCloud.
2. Open the track, playlist, profile, or Likes page you want.
3. Click SoundCloud's `Share` button.
4. Click `Copy Link`.
5. Return to SoundCloud Manager and paste the link into the large URL box.
6. Extra sharing text such as `?si=...` is accepted and removed automatically.

### 6. Download One Track

1. Paste a SoundCloud track link.
2. Click `Use This URL`.
3. Check the artist and title shown under `Track Ready`.
4. Click `Download Track`.
5. Leave the window open until the progress reaches 100%.
6. If SoundCloud cannot supply the audio, the app automatically tries a matching YouTube result.

### 7. Download a Playlist

1. Paste a SoundCloud playlist link containing `/sets/`.
2. Click `Use This URL` and wait while Brave loads the playlist.
3. Review the track list that appears.
4. Leave the checkmark beside every track you want to download.
5. Remove the checkmark beside any track you do not want.
6. Click `Download Selected`.
7. Keep SoundCloud Manager open while it works through the playlist.
8. Watch `Processed X of Y` and the live downloaded, skipped, and failed totals.

### 8. Scrape a Profile or Likes Page

1. Paste a SoundCloud profile link or a link ending in `/likes`.
2. Enter how many tracks to collect in the `Likes limit` box. Use a number from 1 to 100.
3. Click `Use This URL`.
4. Keep the Brave window open while the page is collected.
5. The app creates CSV and Excel files when the organizer finishes.
6. Use the displayed track list if you also want to download selected songs.

### 9. Understand the Results

- `Downloaded` means the MP3 was saved successfully.
- `Skipped` usually means the track was already downloaded.
- `Failed` means neither the SoundCloud source nor the fallback completed.
- `Download complete using YouTube fallback` means SoundCloud failed and the alternate source succeeded.
- A playlist is finished when the status says `Finished` and shows the final totals.

### 10. Find Your Files

1. Open the folder selected in step 4.
2. MP3 downloads are stored directly in that folder.
3. CSV and Excel organizer files are stored with the application output files.
4. Open the Excel workbook to view the cleaned track list, artists, genre sheets, and USB download list.
5. If something did not work, open [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) and find the matching heading.

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
- The progress panel displays live downloaded, skipped, and failed counts after every track, followed by final totals.

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

- Read the complete [`REQUIREMENTS.md`](REQUIREMENTS.md) page before installation.
- **Brave Browser is required for full functionality.** [Download Brave for macOS](https://brave.com/download/).
- Without Brave, direct single-track downloads can still work, but playlists, profiles, Likes scraping, and new scraped Excel workbooks will not work.
- macOS, Python 3, FFmpeg, and internet access are also required.
- The one-time installer checks these items and uses Homebrew to install missing software when possible.

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
