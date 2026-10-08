#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from soundcloud_backend import (
    DOWNLOADS_DIR,
    build_env,
    detect_existing_download,
    download_track,
    ensure_dependencies,
    fetch_metadata,
    is_playlist_url,
    is_profile_or_likes_url,
    is_track_url,
    load_history,
    load_settings,
    normalize_soundcloud_url,
    playlist_entries_from_metadata,
    save_settings,
    track_summary_from_metadata,
    write_playlist_report,
)
from soundcloud_scraper_backend import build_preview_rows, export_workbook, find_brave_path, latest_workbook_for_profile


HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>SoundCloud Music Manager</title>
  <style>
    :root {
      --bg: #f3ecdf;
      --panel: #fffdf8;
      --ink: #15231f;
      --muted: #5a6c64;
      --accent: #c56b2d;
      --accent-dark: #8d4518;
      --nav: #18352f;
      --line: #d8cebd;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Helvetica Neue", sans-serif;
      background: linear-gradient(135deg, #f6efe3 0%, #ece6d6 50%, #efe4d0 100%);
      color: var(--ink);
    }
    .app { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
    .nav {
      background: radial-gradient(circle at top, #24453e 0%, var(--nav) 62%);
      color: white;
      padding: 28px 18px;
    }
    .brand { font-size: 30px; font-weight: 800; line-height: 1.05; margin-bottom: 24px; }
    .nav button {
      width: 100%;
      text-align: left;
      border: 0;
      border-radius: 14px;
      padding: 14px 16px;
      margin-bottom: 8px;
      background: transparent;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }
    .nav button.active, .nav button:hover { background: rgba(255,255,255,0.14); }
    .content { padding: 28px; }
    .view { display: none; animation: fade .22s ease; }
    .view.active { display: block; }
    @keyframes fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    h1 { margin: 0 0 6px; font-size: 34px; }
    .sub { color: var(--muted); margin-bottom: 18px; max-width: 900px; }
    .card {
      background: var(--panel);
      border: 1px solid rgba(0,0,0,0.06);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 12px 30px rgba(36, 28, 11, 0.06);
      margin-bottom: 18px;
    }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
    .field { display: flex; flex-direction: column; gap: 6px; }
    .span-12 { grid-column: span 12; }
    .span-10 { grid-column: span 10; }
    .span-9 { grid-column: span 9; }
    .span-8 { grid-column: span 8; }
    .span-6 { grid-column: span 6; }
    .span-4 { grid-column: span 4; }
    .span-3 { grid-column: span 3; }
    label { font-size: 13px; color: var(--muted); }
    input, select {
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: white;
      font-size: 15px;
    }
    button.primary, button.secondary {
      border: 0;
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 15px;
      cursor: pointer;
    }
    button.primary { background: var(--accent); color: white; }
    button.primary:hover { background: var(--accent-dark); }
    button.secondary { background: #ece4d6; color: var(--ink); }
    .toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .stats { color: var(--muted); margin-top: 8px; }
    .log {
      min-height: 180px;
      max-height: 260px;
      overflow: auto;
      white-space: pre-wrap;
      font-family: Menlo, monospace;
      font-size: 12px;
      background: #141a18;
      color: #d3f3e5;
      border-radius: 14px;
      padding: 14px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      margin-top: 12px;
    }
    th, td {
      border-bottom: 1px solid #eee5d6;
      text-align: left;
      padding: 10px 8px;
      vertical-align: top;
    }
    .muted { color: var(--muted); }
    .status {
      position: fixed;
      left: 280px;
      right: 24px;
      bottom: 16px;
      background: rgba(24, 53, 47, 0.94);
      color: white;
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 14px;
      box-shadow: 0 10px 20px rgba(0,0,0,0.12);
    }
    @media (max-width: 980px) {
      .app { grid-template-columns: 1fr; }
      .nav { position: sticky; top: 0; z-index: 10; }
      .status { left: 16px; right: 16px; }
      .span-10, .span-9, .span-8, .span-6, .span-4, .span-3 { grid-column: span 12; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="nav">
      <div class="brand">SoundCloud<br/>Manager</div>
      <button class="nav-btn active" data-view="single">Single Track</button>
      <button class="nav-btn" data-view="playlist">Playlist</button>
      <button class="nav-btn" data-view="likes">User Likes</button>
      <button class="nav-btn" data-view="scraper">Scraper and Organizer</button>
      <button class="nav-btn" data-view="history">Download History</button>
      <button class="nav-btn" data-view="settings">Settings</button>
    </aside>
    <main class="content">
      <section class="view active" id="view-single">
        <h1>Single Track</h1>
        <div class="sub">Validate one SoundCloud track, preview the detected artist and title, and download through the existing queue.</div>
        <div class="card">
          <div class="grid">
            <div class="field span-10">
              <label>Track URL</label>
              <input id="single-url" placeholder="https://soundcloud.com/artist/track-name" />
            </div>
            <div class="field span-2">
              <label>&nbsp;</label>
              <button class="primary" onclick="detectSingle()">Detect Track</button>
            </div>
          </div>
          <div id="single-meta" class="stats">Track: <span id="single-title">-</span><br/>Artist: <span id="single-artist">-</span></div>
          <div class="toolbar" style="margin-top:14px">
            <button class="secondary" onclick="pickFolder()">Choose Output Folder</button>
            <button class="primary" onclick="downloadSingle()">Download Track</button>
          </div>
        </div>
        <div class="card"><div id="single-log" class="log"></div></div>
      </section>

      <section class="view" id="view-playlist">
        <h1>Playlist</h1>
        <div class="sub">Load a SoundCloud playlist or set, preview tracks before downloading, preserve playlist order, and skip duplicates.</div>
        <div class="card">
          <div class="grid">
            <div class="field span-10">
              <label>Playlist URL</label>
              <input id="playlist-url" placeholder="https://soundcloud.com/artist/sets/playlist-name" />
            </div>
            <div class="field span-2">
              <label>&nbsp;</label>
              <button class="primary" onclick="loadPlaylist()">Load Playlist</button>
            </div>
          </div>
          <div class="toolbar" style="margin-top:14px">
            <button class="secondary" onclick="setAllChecks('playlist-table', true)">Select All</button>
            <button class="secondary" onclick="setAllChecks('playlist-table', false)">Deselect All</button>
            <button class="primary" onclick="downloadPlaylistSelected()">Download Selected</button>
          </div>
          <div id="playlist-count" class="stats">No playlist loaded</div>
          <table id="playlist-table">
            <thead><tr><th></th><th>#</th><th>Artist</th><th>Title</th><th>Status</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
        <div class="card"><div id="playlist-log" class="log"></div></div>
      </section>

      <section class="view" id="view-likes">
        <h1>User Likes</h1>
        <div class="sub">Paste a profile URL or direct Likes URL, cap the run between 1 and 100 tracks, preview results, and optionally download selected tracks.</div>
        <div class="card">
          <div class="grid">
            <div class="field span-8">
              <label>Profile or Likes URL</label>
              <input id="likes-url" placeholder="https://soundcloud.com/username or /likes" />
            </div>
            <div class="field span-2">
              <label>Max tracks</label>
              <input id="likes-limit" type="number" min="1" max="100" value="50" />
            </div>
            <div class="field span-2">
              <label>&nbsp;</label>
              <button class="primary" onclick="previewLikes()">Scrape Preview</button>
            </div>
          </div>
          <div class="toolbar" style="margin-top:14px">
            <button class="secondary" onclick="setAllChecks('likes-table', true)">Select All</button>
            <button class="secondary" onclick="setAllChecks('likes-table', false)">Deselect All</button>
            <button class="primary" onclick="downloadLikesSelected()">Download Selected</button>
          </div>
          <div id="likes-stats" class="stats">No likes run yet</div>
          <table id="likes-table">
            <thead><tr><th></th><th>Artist</th><th>Title</th><th>Status</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
        <div class="card"><div id="likes-log" class="log"></div></div>
      </section>

      <section class="view" id="view-scraper">
        <h1>Scraper and Organizer</h1>
        <div class="sub">Use the existing likes scraper and workbook organizer directly inside the app without rebuilding the workbook structure from scratch.</div>
        <div class="card">
          <div class="grid">
            <div class="field span-10">
              <label>Profile or Likes URL</label>
              <input id="scraper-url" placeholder="https://soundcloud.com/username or /likes" />
            </div>
            <div class="field span-2">
              <label>&nbsp;</label>
              <button class="primary" onclick="runScraper('scrape_only')">Scrape Only</button>
            </div>
          </div>
          <div class="toolbar" style="margin-top:14px">
            <button class="primary" onclick="runScraper('scrape_excel')">Scrape and Create Excel</button>
            <button class="secondary" onclick="openRecentWorkbook()">Open Most Recent Excel</button>
            <button class="secondary" onclick="openOutputFolder()">Open Output Folder</button>
          </div>
          <div id="scraper-result" class="stats">No organizer output yet</div>
        </div>
        <div class="card"><div id="scraper-log" class="log"></div></div>
      </section>

      <section class="view" id="view-history">
        <h1>Download History</h1>
        <div class="sub">Review completed, skipped, and failed downloads across single-track, playlist, and likes workflows.</div>
        <div class="card">
          <div class="toolbar"><button class="secondary" onclick="refreshHistory()">Refresh</button></div>
          <table id="history-table">
            <thead><tr><th>Time</th><th>Source</th><th>Artist</th><th>Title</th><th>Status</th><th>Output</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </section>

      <section class="view" id="view-settings">
        <h1>Settings</h1>
        <div class="sub">Brave Private Browsing is optional and only used for browser-based SoundCloud scraping. The rest of the app still works without Brave installed.</div>
        <div class="card">
          <div class="grid">
            <div class="field span-10">
              <label>Main output folder</label>
              <input id="settings-output" />
            </div>
            <div class="field span-2">
              <label>&nbsp;</label>
              <button class="secondary" onclick="pickFolder()">Choose Folder</button>
            </div>
          </div>
          <div style="margin-top:16px">
            <label><input id="settings-brave" type="checkbox" /> Use Brave Private Browsing for scraping</label>
          </div>
          <div style="margin-top:10px">
            <label><input id="settings-report" type="checkbox" /> Create playlist reports automatically</label>
          </div>
          <div class="toolbar" style="margin-top:16px">
            <button class="primary" onclick="saveSettings()">Save Settings</button>
            <button class="secondary" onclick="checkBrave()">Check Brave</button>
          </div>
          <div id="settings-status" class="stats"></div>
        </div>
      </section>
    </main>
  </div>
  <div class="status" id="status">Ready</div>
  <script>
    let playlistTracks = [];
    let likesTracks = [];

    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('view-' + btn.dataset.view).classList.add('active');
      });
    });

    async function api(path, method='GET', data=null) {
      setStatus('Working...');
      const options = { method, headers: { 'Content-Type': 'application/json' } };
      if (data) options.body = JSON.stringify(data);
      const res = await fetch(path, options);
      const payload = await res.json();
      setStatus(payload.status || 'Ready');
      if (!res.ok) throw new Error(payload.error || 'Request failed');
      return payload;
    }

    function setStatus(text) {
      document.getElementById('status').textContent = text;
    }

    function appendLog(id, text) {
      const box = document.getElementById(id);
      box.textContent += (box.textContent ? "\\n" : "") + text;
      box.scrollTop = box.scrollHeight;
    }

    function setAllChecks(tableId, checked) {
      document.querySelectorAll(`#${tableId} tbody input[type="checkbox"]`).forEach(cb => {
        if (!cb.disabled) cb.checked = checked;
      });
    }

    async function loadSettings() {
      const data = await api('/api/settings');
      document.getElementById('settings-output').value = data.settings.output_folder;
      document.getElementById('settings-brave').checked = !!data.settings.use_brave_private;
      document.getElementById('settings-report').checked = !!data.settings.playlist_report_enabled;
    }

    async function saveSettings() {
      const payload = {
        output_folder: document.getElementById('settings-output').value,
        use_brave_private: document.getElementById('settings-brave').checked,
        playlist_report_enabled: document.getElementById('settings-report').checked,
      };
      await api('/api/settings', 'POST', payload);
      document.getElementById('settings-status').textContent = 'Settings saved.';
    }

    async function pickFolder() {
      const data = await api('/api/pick-folder', 'POST');
      if (data.folder) {
        document.getElementById('settings-output').value = data.folder;
      }
    }

    async function detectSingle() {
      const url = document.getElementById('single-url').value.trim();
      const data = await api('/api/single/detect', 'POST', { url });
      document.getElementById('single-title').textContent = data.track.title || '-';
      document.getElementById('single-artist').textContent = data.track.artist || '-';
      appendLog('single-log', `Detected ${data.track.artist} - ${data.track.title}`);
    }

    async function downloadSingle() {
      const url = document.getElementById('single-url').value.trim();
      const data = await api('/api/single/download', 'POST', { url });
      appendLog('single-log', data.message);
      refreshHistory();
    }

    async function loadPlaylist() {
      const url = document.getElementById('playlist-url').value.trim();
      const data = await api('/api/playlist/load', 'POST', { url });
      playlistTracks = data.tracks;
      document.getElementById('playlist-count').textContent = `${playlistTracks.length} track(s) found`;
      const tbody = document.querySelector('#playlist-table tbody');
      tbody.innerHTML = playlistTracks.map((track, idx) => `
        <tr>
          <td><input type="checkbox" data-idx="${idx}" ${track.already_downloaded ? '' : 'checked'} ${track.already_downloaded ? 'disabled' : ''}></td>
          <td>${track.playlist_index}</td>
          <td>${track.artist || ''}</td>
          <td>${track.title || ''}</td>
          <td>${track.already_downloaded ? 'Skipped' : 'Waiting'}</td>
        </tr>`).join('');
      appendLog('playlist-log', `Loaded ${playlistTracks.length} track(s)`);
    }

    async function downloadPlaylistSelected() {
      const indexes = [...document.querySelectorAll('#playlist-table tbody input:checked')].map(el => Number(el.dataset.idx));
      const selected = indexes.map(i => playlistTracks[i]);
      const data = await api('/api/playlist/download', 'POST', { tracks: selected });
      appendLog('playlist-log', data.message);
      refreshHistory();
    }

    async function previewLikes() {
      const url = document.getElementById('likes-url').value.trim();
      const limit = Number(document.getElementById('likes-limit').value);
      const data = await api('/api/likes/preview', 'POST', { url, limit });
      likesTracks = data.tracks;
      document.getElementById('likes-stats').textContent = data.stats;
      const tbody = document.querySelector('#likes-table tbody');
      tbody.innerHTML = likesTracks.map((track, idx) => `
        <tr>
          <td><input type="checkbox" data-idx="${idx}" ${track.already_downloaded ? '' : 'checked'} ${track.already_downloaded ? 'disabled' : ''}></td>
          <td>${track.artist || ''}</td>
          <td>${track.title || ''}</td>
          <td>${track.already_downloaded ? 'Skipped' : 'Waiting'}</td>
        </tr>`).join('');
      appendLog('likes-log', `Previewed ${likesTracks.length} liked track(s)`);
    }

    async function downloadLikesSelected() {
      const indexes = [...document.querySelectorAll('#likes-table tbody input:checked')].map(el => Number(el.dataset.idx));
      const selected = indexes.map(i => likesTracks[i]);
      const data = await api('/api/likes/download', 'POST', { tracks: selected });
      document.getElementById('likes-stats').textContent = data.stats;
      appendLog('likes-log', data.message);
      refreshHistory();
    }

    async function runScraper(mode) {
      const url = document.getElementById('scraper-url').value.trim();
      const limit = Number(document.getElementById('likes-limit').value || 50);
      const data = await api('/api/scraper/run', 'POST', { url, mode, limit });
      document.getElementById('scraper-result').textContent = data.result;
      appendLog('scraper-log', data.message);
    }

    async function openRecentWorkbook() {
      const url = document.getElementById('scraper-url').value.trim();
      const data = await api('/api/open-workbook', 'POST', { url });
      appendLog('scraper-log', data.message);
    }

    async function openOutputFolder() {
      const data = await api('/api/open-output-folder', 'POST');
      appendLog('scraper-log', data.message);
    }

    async function checkBrave() {
      const data = await api('/api/check-brave', 'POST');
      document.getElementById('settings-status').textContent = data.message;
    }

    async function refreshHistory() {
      const data = await api('/api/history');
      const tbody = document.querySelector('#history-table tbody');
      tbody.innerHTML = data.history.map(item => `
        <tr>
          <td>${item.timestamp || ''}</td>
          <td>${item.source_type || ''}</td>
          <td>${item.artist || ''}</td>
          <td>${item.title || ''}</td>
          <td>${item.status || ''}</td>
          <td class="muted">${item.output_path || ''}</td>
        </tr>`).join('');
    }

    Promise.all([loadSettings(), refreshHistory()]).catch(err => setStatus(err.message));
  </script>
</body>
</html>
"""


class AppState:
    def __init__(self) -> None:
        self.settings = load_settings()

    @property
    def output_folder(self) -> Path:
        return Path(self.settings.get("output_folder", str(DOWNLOADS_DIR))).expanduser()


STATE = AppState()


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    data = handler.rfile.read(length) if length else b"{}"
    return json.loads(data.decode("utf-8") or "{}")


def choose_folder_dialog() -> str:
    script = 'POSIX path of (choose folder with prompt "Choose the main output folder:")'
    result = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def open_path(path: str) -> None:
    subprocess.run(["open", path], check=False)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/settings":
            return json_response(self, {"settings": STATE.settings, "status": "Ready"})
        if parsed.path == "/api/history":
            return json_response(self, {"history": list(reversed(load_history())), "status": "Ready"})
        return json_response(self, {"error": "Not found", "status": "Error"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = read_json(self)
            if parsed.path == "/api/pick-folder":
                folder = choose_folder_dialog()
                if folder:
                    STATE.settings["output_folder"] = folder
                    save_settings(STATE.settings)
                return json_response(self, {"folder": folder, "status": "Ready"})

            if parsed.path == "/api/settings":
                STATE.settings.update(payload)
                save_settings(STATE.settings)
                return json_response(self, {"ok": True, "status": "Settings saved"})

            if parsed.path == "/api/single/detect":
                url = payload.get("url", "").strip()
                if not is_track_url(url):
                    raise RuntimeError("Please enter a valid SoundCloud track URL.")
                track = track_summary_from_metadata(fetch_metadata(url, build_env()), url)
                return json_response(self, {"track": track, "status": "Track detected"})

            if parsed.path == "/api/single/download":
                url = payload.get("url", "").strip()
                if not is_track_url(url):
                    raise RuntimeError("Please enter a valid SoundCloud track URL.")
                env = build_env()
                ensure_dependencies(env)
                result = download_track(url, env, STATE.output_folder, "single")
                return json_response(self, {"message": _result_message(result), "status": "Ready"})

            if parsed.path == "/api/playlist/load":
                url = payload.get("url", "").strip()
                if not is_playlist_url(url):
                    raise RuntimeError("Please enter a SoundCloud playlist or set URL.")
                tracks = playlist_entries_from_metadata(fetch_metadata(url, build_env()))
                for track in tracks:
                    track["already_downloaded"] = bool(detect_existing_download(track["track_url"]))
                return json_response(self, {"tracks": tracks, "status": f"Loaded {len(tracks)} tracks"})

            if parsed.path == "/api/playlist/download":
                env = build_env()
                ensure_dependencies(env)
                selected = payload.get("tracks", [])
                completed = skipped = failed = 0
                report_rows = []
                for track in selected:
                    result = download_track(track["track_url"], env, STATE.output_folder, "playlist")
                    if result.status == "completed":
                        completed += 1
                    elif result.status == "skipped":
                        skipped += 1
                    else:
                        failed += 1
                    report_rows.append(
                        {
                            "track_number": track.get("playlist_index", ""),
                            "artist": result.artist or track.get("artist", ""),
                            "track_title": result.title or track.get("title", ""),
                            "soundcloud_url": track["track_url"],
                            "download_status": result.status.capitalize(),
                            "output_filename": result.output_path,
                            "error_message": result.error or result.skipped_reason,
                        }
                    )
                if STATE.settings.get("playlist_report_enabled", True):
                    report_path = STATE.output_folder / f"playlist_report_{Path(tempfile.mkstemp(prefix='sc_', suffix='.csv')[1]).name}"
                    write_playlist_report(report_path, report_rows)
                return json_response(
                    self,
                    {"message": f"Playlist complete. Downloaded {completed}, skipped {skipped}, failed {failed}.", "status": "Ready"},
                )

            if parsed.path == "/api/likes/preview":
                url = payload.get("url", "").strip()
                limit = int(payload.get("limit", 50))
                if not is_profile_or_likes_url(url):
                    raise RuntimeError("Enter a SoundCloud profile URL or Likes URL.")
                result, rows = build_preview_rows(
                    url,
                    limit,
                    bool(STATE.settings.get("use_brave_private", False)),
                )
                tracks = []
                for idx, row in enumerate(rows, start=1):
                    track_url = row.get("track_url", "")
                    tracks.append(
                        {
                            "playlist_index": idx,
                            "track_url": track_url,
                            "artist": row.get("artist", ""),
                            "title": row.get("title", ""),
                            "already_downloaded": bool(detect_existing_download(track_url)),
                        }
                    )
                stats = (
                    f"Found: {result.found}  New: {result.new}  Previously saved: {result.previously_saved}  "
                    f"Selected: 0  Downloaded: 0  Skipped: 0  Failed: 0"
                )
                return json_response(self, {"tracks": tracks, "stats": stats, "status": "Likes preview ready"})

            if parsed.path == "/api/likes/download":
                env = build_env()
                ensure_dependencies(env)
                selected = payload.get("tracks", [])
                downloaded = skipped = failed = 0
                for track in selected:
                    result = download_track(track["track_url"], env, STATE.output_folder, "likes")
                    if result.status == "completed":
                        downloaded += 1
                    elif result.status == "skipped":
                        skipped += 1
                    else:
                        failed += 1
                stats = (
                    f"Selected: {len(selected)}  Downloaded: {downloaded}  Skipped: {skipped}  Failed: {failed}"
                )
                return json_response(
                    self,
                    {"stats": stats, "message": f"Likes download complete. Downloaded {downloaded}, skipped {skipped}, failed {failed}.", "status": "Ready"},
                )

            if parsed.path == "/api/scraper/run":
                url = payload.get("url", "").strip()
                limit = int(payload.get("limit", 50))
                mode = payload.get("mode", "scrape_only")
                if not is_profile_or_likes_url(url):
                    raise RuntimeError("Enter a SoundCloud profile URL or Likes URL.")
                result, _ = build_preview_rows(url, limit, bool(STATE.settings.get("use_brave_private", False)))
                message = f"Scrape complete. CSV: {result.csv_path}"
                summary = message
                if mode == "scrape_excel":
                    exported = export_workbook(result.csv_path)
                    summary = exported.workbook_path or "Workbook was not created."
                    message = f"Scrape and Excel complete. Workbook: {summary}"
                return json_response(self, {"result": summary, "message": message, "status": "Ready"})

            if parsed.path == "/api/open-workbook":
                url = payload.get("url", "").strip()
                workbook = latest_workbook_for_profile(url)
                if not workbook:
                    raise RuntimeError("No organized workbook was found for that profile yet.")
                open_path(workbook)
                return json_response(self, {"message": f"Opened workbook: {workbook}", "status": "Ready"})

            if parsed.path == "/api/open-output-folder":
                open_path(str(STATE.output_folder))
                return json_response(self, {"message": f"Opened output folder: {STATE.output_folder}", "status": "Ready"})

            if parsed.path == "/api/check-brave":
                brave_path = find_brave_path()
                if brave_path:
                    return json_response(self, {"message": f"Brave found: {brave_path}", "status": "Ready"})
                return json_response(
                    self,
                    {"message": "Brave was not found in /Applications or ~/Applications. Download it from https://brave.com/download/", "status": "Ready"},
                )

            return json_response(self, {"error": "Not found", "status": "Error"}, 404)
        except Exception as exc:
            return json_response(self, {"error": str(exc), "status": "Error"}, 400)

    def log_message(self, format: str, *args) -> None:
        return


def _result_message(result) -> str:
    if result.status == "completed":
        return f"Completed: {result.output_path}"
    if result.status == "skipped":
        return f"Skipped duplicate: {result.output_path or result.url}"
    return f"Failed: {result.error}"


def find_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    port = find_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"SoundCloud Music Manager running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
