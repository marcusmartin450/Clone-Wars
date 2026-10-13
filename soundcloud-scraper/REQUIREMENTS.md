# SoundCloud Manager Requirements

Read this page before installing SoundCloud Manager.

## Most Important: Install Brave Browser

**Brave Browser is required for the complete SoundCloud Manager experience.**

[Download Brave Browser from the official Brave website](https://brave.com/download/)

SoundCloud Manager uses Brave Private Browsing to safely load SoundCloud pages that contain multiple tracks.

Brave is required for:

- Loading and displaying SoundCloud playlists.
- Scraping SoundCloud profiles.
- Scraping SoundCloud Likes pages.
- Collecting track information for CSV files.
- Creating new organized Excel workbooks from scraped pages.

Without Brave:

- The application can still open.
- Direct single-track downloads can still work through `yt-dlp`.
- The YouTube fallback for a direct track can still work.
- Playlist loading will fail.
- Profile and Likes scraping will fail.
- New Excel workbooks cannot be created from those SoundCloud pages.

## Install Brave on a Mac

1. Visit the [official Brave download page](https://brave.com/download/).
2. Download the regular stable version of Brave for macOS.
3. Open the downloaded installer.
4. Drag `Brave Browser` into the Mac's `Applications` folder when asked.
5. Open Brave Browser at least once.
6. Complete or skip Brave's welcome screens.
7. Close Brave, then run `Install SoundCloud Manager.command`.

The SoundCloud Manager installer looks for Brave in either of these standard locations:

```text
/Applications/Brave Browser.app
~/Applications/Brave Browser.app
```

## Mac Requirements

- A Mac running a currently supported version of macOS.
- Permission to install applications.
- Permission to create files in the chosen download folder.
- Enough free storage for the selected MP3 downloads and Excel files.
- A reliable internet connection during installation, scraping, and downloading.

## Required Software

### Python 3

- Python runs the SoundCloud Manager application.
- The installer checks whether Python 3 is available.
- If Python is missing and Homebrew is available, the installer attempts to install it.
- Otherwise, the installer opens the official Python download page.

### FFmpeg

- FFmpeg converts downloaded audio to MP3 and adds artwork and metadata.
- Track downloads cannot finish correctly without FFmpeg.
- The installer attempts to install FFmpeg through Homebrew when possible.

### Homebrew

- Homebrew is strongly recommended but is not part of SoundCloud Manager.
- It allows the installer to add missing Python, Brave, and FFmpeg packages automatically.
- Without Homebrew, the installer directs the user to official manual download pages.

## Python Packages

The one-time installer creates a private `.venv` folder and installs these pinned packages:

```text
openpyxl==3.1.5
playwright==1.58.0
yt-dlp[default]==2026.9.27.232945.dev0
```

- `openpyxl` creates and formats Excel workbooks.
- `playwright` controls Brave for playlist, profile, and Likes collection.
- `yt-dlp` handles SoundCloud downloads and the YouTube fallback.

## Keep the Application Folder Together

- Do not move only `SoundCloud Manager.app` into another folder.
- Keep the app, installer, launcher, Python files, and `.venv` folder together.
- Moving the `.app` by itself prevents it from finding its installed environment.
- You may move the entire extracted `SoundCloud Manager` folder to another location.

## First-Run Checklist

Before opening SoundCloud Manager, confirm:

- [ ] Brave Browser is installed in the Applications folder.
- [ ] Brave has been opened at least once.
- [ ] `Install SoundCloud Manager.command` completed successfully.
- [ ] The SoundCloud Manager folder is still together.
- [ ] The Mac is connected to the internet.
- [ ] There is enough space in the intended download folder.

After opening the GUI:

1. Click `Check Setup`.
2. Confirm that Brave, FFmpeg, Playwright, openpyxl, and yt-dlp were found.
3. Click `Choose Download Folder` and select the destination.
4. Paste a SoundCloud link and begin with a single track or small playlist.

If any check fails, open [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).
