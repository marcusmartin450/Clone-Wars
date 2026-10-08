# SoundCloud Scraper and Organizer

- This is my SoundCloud scraper and organizer.
- I use it to pull tracks from a SoundCloud profile or Likes page.
- It saves the links in a CSV file.
- It organizes the tracks into an Excel workbook.
- This guide only covers the latest app and scraper files.

## What It Does

- Opens SoundCloud in Brave Private Browsing.
- Collects the track, artist, title, genre, download, and buy links.
- Saves new tracks without deleting tracks already collected.
- Creates a cleaned CSV file.
- Creates an Excel workbook with separate genre sheets.
- Puts the genre sheets in alphabetical order.
- Keeps an `All Tracks Cleaned` sheet.
- Keeps a `Genre Mapping` sheet.
- Keeps a `USB Download List` sheet.

## What I Need

- A Mac.
- Python 3.
- Brave Browser.
- The project folder.
- The `.venv` virtual environment.
- Playwright, openpyxl, and yt-dlp installed in the virtual environment.
- Brave installed here:

```text
/Applications/Brave Browser.app
```

## Start the App

- Open Terminal.
- Run:

```bash
cd ~/Music/sdclscript
.venv/bin/python soundcloud_gui.py
```

- The app opens in my web browser.
- The app runs only on my computer through a local address.
- I can also open `scdl.app` from the project folder.

## Turn On Brave Private Browsing

- Open `Settings` in the app.
- Turn on `Use Brave Private Browsing for scraping`.
- Click `Save Settings`.
- Click `Check Brave`.
- The app should say that Brave was found.

## Scrape and Make the Excel File

- Open `User Likes`.
- Set `Max tracks` between 1 and 100.
- The default is 50.
- Open `Scraper and Organizer`.
- Paste a SoundCloud profile or Likes URL.
- Click `Scrape and Create Excel`.
- Let Brave finish loading and collecting the tracks.
- Click `Open Most Recent Excel` when it is done.
- Use `Scrape Only` when I only want to update the main CSV file.
- Example URL:

```text
https://soundcloud.com/marcusmartin450/likes
```

## Files It Creates

- For a profile named `marcusmartin450`, the app creates:

```text
marcusmartin450_likes.csv
marcusmartin450_state.json
marcusmartin450_likes_cleaned.csv
marcusmartin450_likes_organized.xlsx
AddToUSBDownloadList.bas
```

### Main CSV

- `marcusmartin450_likes.csv` is the main saved list.
- New tracks are added to it.
- Tracks already saved are skipped.

### State File

- `marcusmartin450_state.json` keeps information about the last run.
- It also keeps the number of saved tracks.

### Cleaned CSV

- `marcusmartin450_likes_cleaned.csv` removes exact duplicate rows.
- It adds the cleaned genre and website fields.

### Excel Workbook

- `marcusmartin450_likes_organized.xlsx` contains:
- `All Tracks Cleaned`
- `Genre Mapping`
- `USB Download List`
- One sheet for every organized genre
- The genre sheets are arranged alphabetically.
- Tracks with Hypeddit or Hypeedit links are placed under House using my current organizer rule.

## Important Notes

- The app saves up to 100 new tracks in one run.
- Run it again to keep adding new tracks.
- Do not delete the main CSV if I want the scraper to remember tracks already collected.
- A download link can lead to a download page instead of a direct audio file.
- Missing links stay blank.
- The app should not make up a link.
- The app uses `sc_likes_scraper4_organized_outputs.py`.
- Do not use `sc_likes_scraper4_organized_outputs (1).py`.
- The extra copy is not connected to the app.

## If Something Does Not Work

### Brave Is Not Found

- Install Brave in the main Applications folder.
- Use `Settings` > `Check Brave` again.

### A Python Package Is Missing

- Run:

```bash
cd ~/Music/sdclscript
.venv/bin/python -m pip install playwright openpyxl yt-dlp
```

### The App Does Not Open

- Start it from Terminal so I can see the error:

```bash
cd ~/Music/sdclscript
.venv/bin/python soundcloud_gui.py
```

### The Workbook Does Not Open

- Check that this file exists in the project folder:

```text
marcusmartin450_likes_organized.xlsx
```

- Open it directly in Excel.

## Main Files Used by the Latest Version

- `soundcloud_gui.py` runs the app screen.
- `soundcloud_scraper_backend.py` opens Brave and collects the tracks.
- `sc_likes_scraper4_organized_outputs.py` cleans the data and creates the Excel workbook.
- `soundcloud_backend.py` handles settings and downloads.
- The older scraper files are kept for history.
- They are not the version I use for this workflow.
