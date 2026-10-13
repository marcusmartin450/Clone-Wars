#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from soundcloud_backend import (
    DOWNLOADS_DIR,
    build_env,
    download_track,
    ensure_dependencies,
    fetch_metadata,
    is_playlist_url,
    is_profile_or_likes_url,
    is_track_url,
    normalize_soundcloud_url,
    playlist_entries_from_metadata,
    track_summary_from_metadata,
    track_summary_from_url,
)
from soundcloud_scraper_backend import build_preview_rows, export_workbook, find_brave_path


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SoundCloud Manager Easy Start</title>
  <style>
    :root { --green:#18352f; --orange:#c56b2d; --cream:#f3ecdf; --paper:#fffdf8; --line:#d8cebd; --muted:#5a6c64; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Avenir Next","Helvetica Neue",sans-serif; color:var(--green); background:linear-gradient(135deg,#f6efe3,#ece6d6); }
    main { width:min(920px,calc(100% - 32px)); margin:40px auto; }
    h1 { margin:0; font-size:42px; }
    .lead { color:var(--muted); font-size:18px; margin:8px 0 24px; }
    .card { background:var(--paper); border:1px solid rgba(0,0,0,.07); border-radius:20px; padding:22px; margin:16px 0; box-shadow:0 12px 30px rgba(36,28,11,.07); }
    label { display:block; color:var(--muted); margin-bottom:7px; font-size:14px; }
    input { width:100%; padding:14px; border:1px solid var(--line); border-radius:12px; font-size:16px; }
    .row { display:grid; grid-template-columns:1fr 150px; gap:12px; }
    .buttons { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
    button { border:0; border-radius:12px; padding:13px 17px; cursor:pointer; font-size:15px; }
    .primary { background:var(--orange); color:white; }
    .secondary { background:#ece4d6; color:var(--green); }
    .status { padding:12px 14px; border-radius:12px; background:#e8efe9; margin-top:14px; white-space:pre-wrap; }
    .progress-panel { margin-top:14px; display:grid; gap:10px; }
    .progress-item { padding:12px; border:1px solid var(--line); border-radius:12px; background:#fff; }
    .progress-heading { display:flex; justify-content:space-between; gap:12px; margin-bottom:7px; }
    .progress-track { height:12px; overflow:hidden; border-radius:999px; background:#e8dfd0; }
    .progress-fill { height:100%; width:0; background:var(--orange); transition:width .25s ease; }
    .progress-detail { margin-top:6px; color:var(--muted); font-size:13px; }
    .error { background:#f8dddd; color:#7d1f1f; }
    .hidden { display:none; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { text-align:left; border-bottom:1px solid #eee5d6; padding:9px 7px; }
    code { background:#eee7db; padding:2px 5px; border-radius:5px; }
    @media (max-width:700px) { .row { grid-template-columns:1fr; } h1 { font-size:34px; } }
  </style>
</head>
<body>
<main>
  <h1>SoundCloud Manager</h1>
  <div class="lead">Paste one SoundCloud link. The app handles the rest.</div>

  <section class="card">
    <div class="row">
      <div>
        <label for="url">SoundCloud track, playlist, profile, or Likes URL</label>
        <input id="url" placeholder="https://soundcloud.com/..." autofocus />
      </div>
      <div>
        <label for="limit">Likes limit</label>
        <input id="limit" type="number" min="1" max="100" value="50" />
      </div>
    </div>
    <div class="buttons">
      <button class="primary" onclick="runUrl()">Use This URL</button>
      <button class="secondary" onclick="chooseFolder()">Choose Download Folder</button>
      <button class="secondary" onclick="checkSetup()">Check Setup</button>
    </div>
    <div id="status" class="status">Ready. Profiles and Likes pages create CSV and Excel files. Tracks and playlists show a preview before downloading.</div>
    <div id="download-progress" class="progress-panel hidden"></div>
  </section>

  <section id="track-card" class="card hidden">
    <h2>Track Ready</h2>
    <div id="track-info"></div>
    <div class="buttons"><button class="primary" onclick="downloadTrack()">Download Track</button></div>
  </section>

  <section id="playlist-card" class="card hidden">
    <h2>Playlist Ready</h2>
    <div id="playlist-count"></div>
    <table><thead><tr><th></th><th>#</th><th>Artist</th><th>Title</th></tr></thead><tbody id="playlist-body"></tbody></table>
    <div class="buttons"><button class="primary" onclick="downloadPlaylist()">Download Selected</button></div>
  </section>

  <section id="organizer-card" class="card hidden">
    <h2>Organizer Finished</h2>
    <div id="organizer-info"></div>
    <div class="buttons"><button class="secondary" onclick="openWorkbook()">Open Excel File</button></div>
  </section>
</main>
<script>
  let currentTrack = null;
  let playlistTracks = [];
  let workbookPath = '';

  function text(value) {
    return String(value || '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }

  function setStatus(message, isError=false) {
    const box = document.getElementById('status');
    box.textContent = message;
    box.classList.toggle('error', isError);
  }

  function hideResults() {
    ['track-card','playlist-card','organizer-card'].forEach(id => document.getElementById(id).classList.add('hidden'));
  }

  function renderDownloadProgress(job) {
    const panel = document.getElementById('download-progress');
    panel.classList.remove('hidden');
    panel.innerHTML = (job.tracks || []).map(track => {
      const percent = Math.max(0, Math.min(100, Number(track.percent || 0)));
      const name = [track.artist, track.title].filter(Boolean).join(' - ') || track.url;
      return `<div class="progress-item">
        <div class="progress-heading"><strong>${text(name)}</strong><span>${Math.round(percent)}%</span></div>
        <div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div>
        <div class="progress-detail">${text(track.detail || track.status || 'Waiting')}</div>
      </div>`;
    }).join('');
  }

  async function watchDownload(jobId) {
    while (true) {
      const response = await fetch(`/api/progress?job_id=${encodeURIComponent(jobId)}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Could not read download progress.');
      renderDownloadProgress(payload.job);
      if (payload.job.status !== 'running') {
        setStatus(payload.job.message, payload.job.failed > 0);
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  async function startDownload(tracks) {
    if (!tracks.length) {
      setStatus('Select at least one song.', true);
      return;
    }
    const panel = document.getElementById('download-progress');
    panel.innerHTML = '';
    panel.classList.remove('hidden');
    const data = await api('/api/download', {tracks});
    await watchDownload(data.job_id);
  }

  async function api(path, data={}) {
    setStatus('Working... Keep this window open.');
    const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'The request failed.');
    setStatus(payload.status || 'Ready.');
    return payload;
  }

  async function runUrl() {
    hideResults();
    try {
      const url = document.getElementById('url').value.trim();
      const limit = Number(document.getElementById('limit').value || 50);
      const data = await api('/api/run', {url, limit});
      if (data.kind === 'track') {
        currentTrack = data.track;
        document.getElementById('track-info').innerHTML = `<strong>${text(data.track.artist)} - ${text(data.track.title)}</strong><br><code>${text(data.track.track_url)}</code>`;
        document.getElementById('track-card').classList.remove('hidden');
      } else if (data.kind === 'playlist') {
        playlistTracks = data.tracks;
        document.getElementById('playlist-count').textContent = `${playlistTracks.length} track(s) found.`;
        document.getElementById('playlist-body').innerHTML = playlistTracks.map((track,index) => `<tr><td><input type="checkbox" data-index="${index}" checked></td><td>${text(track.playlist_index)}</td><td>${text(track.artist)}</td><td>${text(track.title)}</td></tr>`).join('');
        document.getElementById('playlist-card').classList.remove('hidden');
      } else {
        workbookPath = data.workbook_path;
        document.getElementById('organizer-info').textContent = `Saved ${data.new_tracks} new track(s). Excel file: ${workbookPath}`;
        document.getElementById('organizer-card').classList.remove('hidden');
      }
    } catch (error) { setStatus(error.message, true); }
  }

  async function downloadTrack() {
    try { await startDownload([currentTrack]); }
    catch (error) { setStatus(error.message, true); }
  }

  async function downloadPlaylist() {
    const indexes = [...document.querySelectorAll('#playlist-body input:checked')].map(box => Number(box.dataset.index));
    try { await startDownload(indexes.map(index => playlistTracks[index])); }
    catch (error) { setStatus(error.message, true); }
  }

  async function chooseFolder() {
    try { const data = await api('/api/folder'); setStatus(data.folder ? `Downloads will be saved in ${data.folder}` : 'Folder selection cancelled.'); }
    catch (error) { setStatus(error.message, true); }
  }

  async function checkSetup() {
    try { const data = await api('/api/check'); setStatus(data.message, !data.ready); }
    catch (error) { setStatus(error.message, true); }
  }

  async function openWorkbook() {
    try { await api('/api/open', {path:workbookPath}); }
    catch (error) { setStatus(error.message, true); }
  }
</script>
</body>
</html>
"""


OUTPUT_FOLDER = DOWNLOADS_DIR
DOWNLOAD_JOBS: dict[str, dict] = {}
DOWNLOAD_JOBS_LOCK = threading.Lock()
DOWNLOAD_PERCENT_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")


def update_download_job(job_id: str, track_index: int | None = None, **changes) -> None:
    with DOWNLOAD_JOBS_LOCK:
        job = DOWNLOAD_JOBS[job_id]
        target = job if track_index is None else job["tracks"][track_index]
        target.update(changes)


def download_progress_update(job_id: str, track_index: int, output: str) -> None:
    match = DOWNLOAD_PERCENT_RE.search(output)
    changes = {"detail": output[-180:]}
    if match:
        changes.update(status="downloading", percent=float(match.group(1)))
    elif "[ExtractAudio]" in output or "[Metadata]" in output or "[EmbedThumbnail]" in output:
        changes.update(status="finishing", percent=98)
    update_download_job(job_id, track_index, **changes)


def download_counts_message(current: int, total: int, completed: int, skipped: int, failed: int) -> str:
    return (
        f"Processed {current} of {total}. "
        f"Downloaded {completed}, skipped {skipped}, failed {failed}."
    )


def run_download_job(job_id: str, tracks: list[dict], target_folder: Path) -> None:
    completed = skipped = failed = 0
    try:
        env = build_env()
        ensure_dependencies(env)
        for index, track in enumerate(tracks):
            current = index + 1
            update_download_job(
                job_id,
                current=current,
                message=download_counts_message(index, len(tracks), completed, skipped, failed),
            )
            update_download_job(job_id, index, status="preparing", detail="Preparing download...", percent=0)
            result = download_track(
                track.get("track_url", ""),
                env,
                target_folder,
                "easy",
                lambda output, current=index: download_progress_update(job_id, current, output),
                track_info=track,
            )
            if result.status == "completed":
                completed += 1
                detail = "Download complete"
                if result.download_source == "youtube":
                    detail = "Download complete using YouTube fallback"
                update_download_job(job_id, index, status="completed", detail=detail, percent=100)
            elif result.status == "skipped":
                skipped += 1
                update_download_job(job_id, index, status="skipped", detail=result.skipped_reason or "Skipped", percent=100)
            else:
                failed += 1
                update_download_job(job_id, index, status="failed", detail=result.error or "Download failed", percent=0)
            update_download_job(
                job_id,
                completed=completed,
                skipped=skipped,
                failed=failed,
                current=current,
                message=download_counts_message(current, len(tracks), completed, skipped, failed),
            )
    except Exception as exc:
        failed += 1
        update_download_job(job_id, status="failed", error=str(exc))

    message = f"Finished. Downloaded {completed}, skipped {skipped}, failed {failed}."
    update_download_job(
        job_id,
        status="finished",
        completed=completed,
        skipped=skipped,
        failed=failed,
        message=message,
    )


def start_download_job(tracks: list[dict], target_folder: Path) -> str:
    job_id = uuid.uuid4().hex
    job_tracks = [
        {
            "url": track.get("track_url", ""),
            "artist": track.get("artist", ""),
            "title": track.get("title", ""),
            "status": "waiting",
            "detail": "Waiting...",
            "percent": 0,
        }
        for track in tracks
    ]
    with DOWNLOAD_JOBS_LOCK:
        DOWNLOAD_JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "tracks": job_tracks,
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "current": 0,
            "total": len(tracks),
            "message": "Downloads are running.",
        }
    threading.Thread(target=run_download_job, args=(job_id, tracks, target_folder), daemon=True).start()
    return job_id


def download_job_snapshot(job_id: str) -> dict | None:
    with DOWNLOAD_JOBS_LOCK:
        job = DOWNLOAD_JOBS.get(job_id)
        return json.loads(json.dumps(job)) if job else None


def classify_soundcloud_url(url: str) -> tuple[str, str]:
    normalized = normalize_soundcloud_url(url)
    if is_playlist_url(normalized):
        return "playlist", normalized
    if is_profile_or_likes_url(normalized):
        return "profile", normalized
    if is_track_url(normalized):
        return "track", normalized
    raise RuntimeError("Paste a SoundCloud track, playlist, profile, or Likes URL.")


def choose_folder() -> str:
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", 'POSIX path of (choose folder with prompt "Choose where downloads should be saved:")'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def setup_message() -> tuple[bool, str]:
    missing = []
    if not find_brave_path():
        missing.append("Brave Browser")
    if shutil.which("ffmpeg", path=build_env().get("PATH")) is None:
        missing.append("FFmpeg")
    try:
        import openpyxl  # noqa: F401
        import playwright  # noqa: F401
        import yt_dlp  # noqa: F401
    except ImportError as exc:
        missing.append(str(exc).replace("No module named ", "Python package "))
    if missing:
        return False, "Setup still needs: " + ", ".join(missing) + ". Run Install SoundCloud Manager.command."
    return True, "Setup is ready. Brave, FFmpeg, Playwright, openpyxl, and yt-dlp were found."


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length) if length else b"{}"
    return json.loads(body.decode("utf-8") or "{}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/progress":
            job_id = parse_qs(parsed.query).get("job_id", [""])[0]
            job = download_job_snapshot(job_id)
            if not job:
                return json_response(self, {"error": "Download job not found."}, 404)
            return json_response(self, {"job": job})
        if parsed.path != "/":
            return json_response(self, {"error": "Not found"}, 404)
        body = HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        global OUTPUT_FOLDER
        try:
            path = urlparse(self.path).path
            payload = read_json(self)
            if path == "/api/run":
                kind, url = classify_soundcloud_url(payload.get("url", ""))
                if kind == "track":
                    try:
                        track = track_summary_from_metadata(fetch_metadata(url, build_env()), url)
                        status = "Track ready."
                    except RuntimeError:
                        track = track_summary_from_url(url)
                        status = "SoundCloud preview unavailable. Track ready for YouTube fallback."
                    return json_response(self, {"kind": kind, "track": track, "status": status})
                if kind == "playlist":
                    tracks = playlist_entries_from_metadata(fetch_metadata(url, build_env()))
                    return json_response(self, {"kind": kind, "tracks": tracks, "status": f"Playlist ready with {len(tracks)} tracks."})
                limit = int(payload.get("limit", 50))
                result, _ = build_preview_rows(url, limit, True)
                exported = export_workbook(result.csv_path)
                return json_response(
                    self,
                    {
                        "kind": kind,
                        "new_tracks": result.new,
                        "csv_path": result.csv_path,
                        "workbook_path": str(Path(exported.workbook_path).resolve()),
                        "status": "Scrape and Excel organizer finished.",
                    },
                )
            if path == "/api/download":
                tracks = payload.get("tracks") or []
                if not tracks:
                    raise RuntimeError("Select at least one track.")
                job_id = start_download_job(tracks, OUTPUT_FOLDER)
                return json_response(self, {"job_id": job_id, "status": "Download started."})
            if path == "/api/folder":
                folder = choose_folder()
                if folder:
                    OUTPUT_FOLDER = Path(folder).expanduser()
                return json_response(self, {"folder": folder, "status": "Folder ready."})
            if path == "/api/check":
                ready, message = setup_message()
                return json_response(self, {"ready": ready, "message": message, "status": "Setup checked."})
            if path == "/api/open":
                target = Path(payload.get("path", "")).expanduser()
                if not target.exists():
                    raise RuntimeError("The Excel file could not be found.")
                subprocess.run(["open", str(target)], check=False)
                return json_response(self, {"status": "Excel file opened."})
            return json_response(self, {"error": "Not found"}, 404)
        except Exception as exc:
            return json_response(self, {"error": str(exc), "status": "Error"}, 400)

    def log_message(self, format: str, *args) -> None:
        return


def find_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    port = find_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    print(f"SoundCloud Manager Easy Start running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
