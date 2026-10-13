from __future__ import annotations

import soundcloud_easy_gui as app
from soundcloud_artist_extension import install_artist_index
from soundcloud_download_jobs import install_download_jobs
from soundcloud_easy_features import install_profile_downloads
from soundcloud_exact_downloader import download_track_exact
from soundcloud_playlist_browser import fetch_playlist_metadata_with_brave


original_fetch_metadata = app.fetch_metadata


def fetch_metadata_with_playlist_fallback(url: str, env=None):
    if app.is_playlist_url(url):
        return fetch_playlist_metadata_with_brave(url, env)
    return original_fetch_metadata(url, env)


install_artist_index()
install_profile_downloads(app)
install_download_jobs(app)
app.fetch_metadata = fetch_metadata_with_playlist_fallback
app.download_track = download_track_exact


if __name__ == "__main__":
    raise SystemExit(app.main())
