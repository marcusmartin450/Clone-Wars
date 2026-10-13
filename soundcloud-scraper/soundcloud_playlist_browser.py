from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

import sc_likes_scraper4_organized_outputs as organizer
from soundcloud_scraper_backend import find_brave_path


def fetch_playlist_metadata_with_brave(url: str, _env=None, limit: int = 100) -> dict[str, object]:
    brave_path = find_brave_path()
    if not brave_path:
        raise RuntimeError("Brave Browser is required to load this playlist.")

    playlist_path = urlparse(url).path.strip("/")
    collected: dict[str, dict] = {}
    idle_rounds = 0
    previous_count = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            executable_path=brave_path,
            args=[
                "--incognito",
                "--autoplay-policy=user-gesture-required",
                "--disable-component-update",
            ],
        )
        context = browser.new_context()
        page = context.new_page()
        organizer.configure_guest_metadata_page(context, page)
        page.goto(url, wait_until="domcontentloaded", timeout=organizer.PAGE_TIMEOUT_MS)
        page.wait_for_timeout(5000)
        organizer.dismiss_guest_sign_in_prompt(page)

        while len(collected) < limit and idle_rounds < 6:
            organizer.dismiss_guest_sign_in_prompt(page)
            links = page.locator('a[href*="?in="]').evaluate_all(
                """(anchors, playlistPath) => anchors.map(anchor => ({
                    href: anchor.href,
                    title: (anchor.innerText || anchor.textContent || '').replace(/\\s+/g, ' ').trim()
                })).filter(item => {
                    try {
                        return new URL(item.href).searchParams.get('in') === playlistPath;
                    } catch (_) {
                        return false;
                    }
                })""",
                playlist_path,
            )
            for item in links:
                track_url = organizer.normalize_url(item.get("href"))
                if track_url and organizer.is_track_url(track_url):
                    artist_slug = urlparse(track_url).path.strip("/").split("/")[0]
                    collected[track_url] = {
                        "webpage_url": track_url,
                        "title": item.get("title") or "",
                        "artist": artist_slug.replace("-", " "),
                    }
                    if len(collected) >= limit:
                        break

            if len(collected) == previous_count:
                idle_rounds += 1
            else:
                idle_rounds = 0
                previous_count = len(collected)

            page.mouse.wheel(0, organizer.NORMAL_SCROLL_PIXELS)
            page.wait_for_timeout(organizer.WAIT_MS)

        browser.close()

    if not collected:
        raise RuntimeError("No playlist tracks were found. The playlist may be private or unavailable.")
    return {"entries": list(collected.values())}
