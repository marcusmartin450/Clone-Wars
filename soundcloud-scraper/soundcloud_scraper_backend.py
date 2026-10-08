from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright

import sc_likes_scraper4_organized_outputs as organizer
from soundcloud_backend import build_likes_url, is_profile_or_likes_url, load_settings, utc_now_iso


BRAVE_CANDIDATES = [
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    str(Path.home() / "Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
]


@dataclass
class LikesRunResult:
    csv_path: str
    state_path: str
    workbook_path: str = ""
    cleaned_csv_path: str = ""
    found: int = 0
    new: int = 0
    previously_saved: int = 0
    selected: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0


def find_brave_path() -> str | None:
    for candidate in BRAVE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None


def read_csv_rows(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scrape_likes(
    profile_or_likes_url: str,
    max_new_urls: int,
    use_brave_private: bool,
    progress_callback: Callable[[str], None] | None = None,
) -> LikesRunResult:
    if not is_profile_or_likes_url(profile_or_likes_url):
        raise RuntimeError("Please enter a SoundCloud profile URL or Likes URL.")
    if max_new_urls < 1 or max_new_urls > 100:
        raise RuntimeError("Likes collection limit must be between 1 and 100.")

    likes_url = build_likes_url(profile_or_likes_url)
    profile_slug, csv_file, state_file = organizer.build_output_paths(profile_or_likes_url)
    organizer.ensure_csv_exists(csv_file)
    seen_urls = organizer.load_existing_track_urls(csv_file)
    previous_count = len(seen_urls)
    pending_rows: list[dict] = []
    total_new = 0
    total_found = 0
    idle_rounds = 0
    cycle = 0
    previous_candidate_count = 0
    duplicate_only_rounds = 0
    scrape_complete = False

    brave_path = find_brave_path() if use_brave_private else None
    if use_brave_private and not brave_path:
        raise RuntimeError("Brave Browser was not found in /Applications or ~/Applications.")

    if progress_callback:
        progress_callback(f"Opening {likes_url}")

    with sync_playwright() as playwright:
        launch_kwargs = {"headless": False}
        if brave_path:
            launch_kwargs["executable_path"] = brave_path
            launch_kwargs["args"] = ["--incognito"]
        browser = playwright.chromium.launch(**launch_kwargs)
        context = browser.new_context()
        page = context.new_page()
        page.goto(likes_url, wait_until="domcontentloaded", timeout=organizer.PAGE_TIMEOUT_MS)
        page.wait_for_timeout(5000)

        while True:
            cycle += 1
            candidate_tracks = organizer.extract_visible_track_data(page)
            total_found = max(total_found, len(candidate_tracks))
            cycle_new = 0

            for track in candidate_tracks:
                track_url = organizer.normalize_url(track.get("track_url"))
                if not track_url or not organizer.is_track_url(track_url):
                    continue
                if track_url in seen_urls:
                    continue

                row = organizer.build_csv_row(track, likes_url)
                if not row:
                    continue

                seen_urls.add(track_url)
                pending_rows.append(row)
                cycle_new += 1
                total_new += 1

                if total_new >= max_new_urls:
                    break

            if progress_callback:
                progress_callback(
                    f"Cycle {cycle}: found {len(candidate_tracks)} visible tracks, {cycle_new} new, total new {total_new}"
                )

            if len(pending_rows) >= organizer.BATCH_SIZE or total_new >= max_new_urls:
                organizer.append_rows(csv_file, pending_rows)
                pending_rows.clear()
                organizer.save_state(
                    state_file,
                    organizer.make_state_dict(
                        profile_slug,
                        likes_url,
                        csv_file,
                        len(seen_urls),
                        total_new,
                        max_new_urls,
                        False,
                    ),
                )

            if total_new >= max_new_urls:
                break

            if len(candidate_tracks) == previous_candidate_count:
                idle_rounds += 1
            else:
                idle_rounds = 0
                previous_candidate_count = len(candidate_tracks)

            if cycle_new == 0 and candidate_tracks:
                duplicate_only_rounds += 1
            else:
                duplicate_only_rounds = 0

            if idle_rounds >= organizer.MAX_IDLE_ROUNDS:
                scrape_complete = True
                break

            if duplicate_only_rounds >= organizer.DUPLICATE_ONLY_THRESHOLD:
                scroll_pixels = organizer.FAST_SCROLL_PIXELS
                wait_ms = organizer.FAST_SCROLL_WAIT_MS
            else:
                scroll_pixels = organizer.NORMAL_SCROLL_PIXELS
                wait_ms = organizer.WAIT_MS

            page.mouse.wheel(0, scroll_pixels)
            page.wait_for_timeout(wait_ms)

        if pending_rows:
            organizer.append_rows(csv_file, pending_rows)

        organizer.save_state(
            state_file,
            organizer.make_state_dict(
                profile_slug,
                likes_url,
                csv_file,
                len(seen_urls),
                total_new,
                max_new_urls,
                scrape_complete,
            ),
        )
        browser.close()

    return LikesRunResult(
        csv_path=csv_file,
        state_path=state_file,
        found=total_found,
        new=total_new,
        previously_saved=previous_count,
    )


def build_preview_rows(profile_or_likes_url: str, max_new_urls: int, use_brave_private: bool, progress_callback=None):
    result = scrape_likes(profile_or_likes_url, max_new_urls, use_brave_private, progress_callback)
    rows = read_csv_rows(result.csv_path)
    likes_url = build_likes_url(profile_or_likes_url)
    new_rows = [row for row in rows if row.get("source_profile") == likes_url][-max_new_urls:]
    return result, new_rows


def export_workbook(csv_path: str) -> LikesRunResult:
    cleaned_csv_path, cleaned_rows, fieldnames = organizer.write_cleaned_csv(csv_path)
    workbook_path = organizer.write_organized_workbook(csv_path, cleaned_rows, fieldnames)
    organizer.write_usb_macro_bas("AddToUSBDownloadList.bas")
    return LikesRunResult(
        csv_path=csv_path,
        state_path=csv_path.replace("_likes.csv", "_state.json"),
        workbook_path=workbook_path or "",
        cleaned_csv_path=cleaned_csv_path,
        found=len(cleaned_rows),
        new=0,
        previously_saved=max(0, len(cleaned_rows)),
    )


def latest_workbook_for_profile(profile_or_likes_url: str) -> str:
    _, csv_file, _ = organizer.build_output_paths(profile_or_likes_url)
    workbook_path = csv_file.replace(".csv", "_organized.xlsx")
    return workbook_path if os.path.exists(workbook_path) else ""
