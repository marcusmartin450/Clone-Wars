from __future__ import annotations

from urllib.parse import urlparse


PROFILE_PANEL = """
    <div id="profile-downloads" class="hidden">
      <h3>Scraped Tracks</h3>
      <div id="profile-count"></div>
      <table>
        <thead><tr><th></th><th>Artist</th><th>Title</th></tr></thead>
        <tbody id="profile-body"></tbody>
      </table>
      <div class="buttons"><button class="primary" onclick="downloadProfileSelected()">Download Selected Songs</button></div>
    </div>
"""


PROFILE_SCRIPT = r"""
  let profileTracks = [];

  async function loadProfileTracks() {
    try {
      const data = await api('/api/profile/tracks');
      profileTracks = data.tracks || [];
      document.getElementById('profile-count').textContent = `${profileTracks.length} track(s) ready to download.`;
      document.getElementById('profile-body').innerHTML = profileTracks.map((track,index) => `<tr><td><input type="checkbox" data-index="${index}" checked></td><td>${text(track.artist)}</td><td>${text(track.title)}</td></tr>`).join('');
      document.getElementById('profile-downloads').classList.toggle('hidden', profileTracks.length === 0);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function downloadProfileSelected() {
    const indexes = [...document.querySelectorAll('#profile-body input:checked')].map(box => Number(box.dataset.index));
    if (!indexes.length) {
      setStatus('Select at least one song.', true);
      return;
    }
    try {
      await startDownload(indexes.map(index => profileTracks[index]));
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  const organizerObserver = new MutationObserver(() => {
    const card = document.getElementById('organizer-card');
    if (!card.classList.contains('hidden') && workbookPath) loadProfileTracks();
  });
  organizerObserver.observe(document.getElementById('organizer-card'), {attributes:true, attributeFilter:['class']});
"""


def install_profile_downloads(app) -> None:
    latest_tracks: list[dict] = []
    original_preview = app.build_preview_rows
    original_post = app.Handler.do_POST

    def preview_and_capture(*args, **kwargs):
        nonlocal latest_tracks
        result, rows = original_preview(*args, **kwargs)
        latest_tracks = [
            {
                "track_url": row.get("track_url", ""),
                "artist": row.get("artist", ""),
                "title": row.get("title", ""),
            }
            for row in rows
            if row.get("track_url")
        ]
        return result, rows

    def do_post_with_profile_tracks(handler):
        if urlparse(handler.path).path == "/api/profile/tracks":
            return app.json_response(
                handler,
                {"tracks": latest_tracks, "status": f"{len(latest_tracks)} scraped track(s) ready."},
            )
        return original_post(handler)

    app.build_preview_rows = preview_and_capture
    app.Handler.do_POST = do_post_with_profile_tracks
    app.HTML = app.HTML.replace(
        "  </section>\n</main>",
        PROFILE_PANEL + "  </section>\n</main>",
        1,
    )
    app.HTML = app.HTML.replace("</script>", PROFILE_SCRIPT + "\n</script>", 1)
