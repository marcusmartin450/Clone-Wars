from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
DOWNLOADS_DIR = Path.home() / "Downloads"
COMMON_BIN_DIRS = ["/usr/local/bin", "/opt/homebrew/bin"]
BUNDLED_YTDLP_DIR = PROJECT_DIR / "yt_dlp"
APP_DATA_DIR = PROJECT_DIR / ".app_data"
SETTINGS_PATH = APP_DATA_DIR / "settings.json"
HISTORY_PATH = APP_DATA_DIR / "download_history.json"
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")
DEFAULT_SETTINGS = {
    "output_folder": str(DOWNLOADS_DIR),
    "use_brave_private": False,
    "playlist_report_enabled": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_app_data_dir() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception:
        pass
    return default


def save_json(path: Path, data) -> None:
    ensure_app_data_dir()
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    os.replace(temp_path, path)


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    settings.update(load_json(SETTINGS_PATH, {}))
    return settings


def save_settings(settings: dict) -> None:
    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings)
    save_json(SETTINGS_PATH, merged)


def load_history() -> list[dict]:
    history = load_json(HISTORY_PATH, [])
    return history if isinstance(history, list) else []


def append_history(entry: dict) -> None:
    history = load_history()
    history.append(entry)
    save_json(HISTORY_PATH, history[-5000:])


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    path_parts = env.get("PATH", "").split(os.pathsep) if env.get("PATH") else []
    for bin_dir in reversed(COMMON_BIN_DIRS):
        if bin_dir not in path_parts:
            path_parts.insert(0, bin_dir)
    env["PATH"] = os.pathsep.join(part for part in path_parts if part)
    if BUNDLED_YTDLP_DIR.exists():
        current_pythonpath = env.get("PYTHONPATH", "")
        pythonpath_parts = current_pythonpath.split(os.pathsep) if current_pythonpath else []
        project_dir = str(PROJECT_DIR)
        if project_dir not in pythonpath_parts:
            pythonpath_parts.insert(0, project_dir)
        env["PYTHONPATH"] = os.pathsep.join(part for part in pythonpath_parts if part)
    return env


def ytdlp_base_command() -> list[str]:
    if VENV_PYTHON.exists():
        return [str(VENV_PYTHON), "-m", "yt_dlp"]
    if shutil.which(sys.executable):
        return [sys.executable, "-m", "yt_dlp"]
    raise RuntimeError("yt-dlp is not available in the project virtualenv.")


def ensure_dependencies(env: dict[str, str]) -> None:
    if shutil.which("ffmpeg", path=env["PATH"]) is None:
        raise RuntimeError("FFmpeg is not available on PATH.")


def sanitize_filename_part(value: str | None, fallback: str) -> str:
    text = (value or "").strip()
    text = INVALID_FILENAME_CHARS.sub(" ", text)
    text = WHITESPACE.sub(" ", text).strip(" .")
    return text or fallback


def first_non_empty(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return None


def choose_filename(info: dict[str, object]) -> str:
    artist = sanitize_filename_part(
        first_non_empty(
            info.get("artist"),
            info.get("uploader"),
            info.get("creator"),
            info.get("channel"),
            info.get("album_artist"),
        ),
        "Unknown Artist",
    )
    title = sanitize_filename_part(
        first_non_empty(
            info.get("track"),
            info.get("title"),
            info.get("fulltitle"),
            info.get("alt_title"),
        ),
        "Unknown Track",
    )
    return f"{artist} - {title}"


def unique_target(target_dir: Path, stem: str, extension: str) -> Path:
    candidate = target_dir / f"{stem}.{extension}"
    suffix = 2
    while candidate.exists():
        candidate = target_dir / f"{stem} ({suffix}).{extension}"
        suffix += 1
    return candidate


def normalize_soundcloud_url(url: str) -> str:
    return url.strip().split("?")[0].split("#")[0].rstrip("/")


def is_soundcloud_url(url: str) -> bool:
    return normalize_soundcloud_url(url).startswith("https://soundcloud.com/")


def is_track_url(url: str) -> bool:
    url = normalize_soundcloud_url(url)
    if not is_soundcloud_url(url):
        return False
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    if len(parts) != 2:
        return False
    banned_first = {
        "you", "discover", "stream", "upload", "search", "charts", "stations",
        "genres", "tags", "pages", "company", "jobs", "imprint", "terms-of-use",
        "about", "blog", "mobile", "download", "developers", "support", "legal",
        "copyright", "press", "newsroom", "advertising", "pro", "for-artists",
        "community", "go", "accounts", "settings",
    }
    banned_second = {
        "likes", "followers", "following", "library", "tracks", "albums",
        "reposts", "spotlight", "sets", "privacy", "cookies", "newsroom",
        "getheard", "terms", "about", "jobs", "developers", "blog", "mobile",
        "download", "legal", "copyright",
    }
    return parts[0].lower() not in banned_first and parts[1].lower() not in banned_second


def is_playlist_url(url: str) -> bool:
    url = normalize_soundcloud_url(url)
    if not is_soundcloud_url(url):
        return False
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    return len(parts) >= 3 and parts[1].lower() in {"sets", "albums"}


def build_likes_url(profile_or_likes_url: str) -> str:
    url = normalize_soundcloud_url(profile_or_likes_url)
    if url.endswith("/likes"):
        return url
    return f"{url}/likes"


def is_profile_or_likes_url(url: str) -> bool:
    url = normalize_soundcloud_url(url)
    if not is_soundcloud_url(url):
        return False
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    if not parts:
        return False
    return len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == "likes")


def fetch_metadata(url: str, env: dict[str, str] | None = None) -> dict[str, object]:
    env = env or build_env()
    command = ytdlp_base_command() + ["--dump-single-json", "--skip-download", url]
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "yt-dlp metadata lookup failed.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"yt-dlp returned invalid metadata JSON: {exc}") from exc


def playlist_entries_from_metadata(metadata: dict[str, object]) -> list[dict]:
    entries = metadata.get("entries")
    if not isinstance(entries, list):
        return []
    results = []
    seen = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            continue
        url = first_non_empty(entry.get("webpage_url"), entry.get("url"), entry.get("original_url"))
        if not isinstance(url, str):
            continue
        normalized = normalize_soundcloud_url(url)
        if not is_track_url(normalized) or normalized in seen:
            continue
        seen.add(normalized)
        results.append(
            {
                "playlist_index": index,
                "track_url": normalized,
                "title": first_non_empty(entry.get("track"), entry.get("title")) or "",
                "artist": first_non_empty(entry.get("artist"), entry.get("uploader"), entry.get("creator")) or "",
                "artwork_url": first_non_empty(entry.get("thumbnail"), entry.get("artwork_url")) or "",
            }
        )
    return results


def detect_existing_download(url: str, target_dir: Path | None = None) -> dict | None:
    normalized = normalize_soundcloud_url(url)
    for entry in reversed(load_history()):
        if normalize_soundcloud_url(entry.get("url", "")) != normalized:
            continue
        if entry.get("status") != "completed":
            continue
        output_path = entry.get("output_path")
        if output_path and Path(output_path).exists():
            if target_dir is None or Path(output_path).parent == target_dir:
                return entry
    return None


def track_summary_from_metadata(metadata: dict[str, object], url: str) -> dict:
    return {
        "track_url": normalize_soundcloud_url(url),
        "title": first_non_empty(metadata.get("track"), metadata.get("title")) or "",
        "artist": first_non_empty(metadata.get("artist"), metadata.get("uploader"), metadata.get("creator")) or "",
        "artwork_url": first_non_empty(metadata.get("thumbnail"), metadata.get("artwork_url")) or "",
    }


@dataclass
class DownloadResult:
    url: str
    status: str
    artist: str = ""
    title: str = ""
    output_path: str = ""
    error: str = ""
    skipped_reason: str = ""

    def to_history_entry(self, source_type: str, target_dir: Path) -> dict:
        data = asdict(self)
        data["source_type"] = source_type
        data["target_dir"] = str(target_dir)
        data["timestamp"] = utc_now_iso()
        return data


def download_track(
    url: str,
    env: dict[str, str],
    target_dir: Path,
    source_type: str = "single",
    progress_callback: Callable[[str], None] | None = None,
) -> DownloadResult:
    normalized = normalize_soundcloud_url(url)
    duplicate = detect_existing_download(normalized)
    if duplicate:
        result = DownloadResult(
            url=normalized,
            status="skipped",
            artist=duplicate.get("artist", ""),
            title=duplicate.get("title", ""),
            output_path=duplicate.get("output_path", ""),
            skipped_reason="Already downloaded",
        )
        append_history(result.to_history_entry(source_type, target_dir))
        return result

    target_dir.mkdir(parents=True, exist_ok=True)
    metadata = fetch_metadata(normalized, env)
    title = first_non_empty(metadata.get("track"), metadata.get("title")) or ""
    artist = first_non_empty(metadata.get("artist"), metadata.get("uploader"), metadata.get("creator")) or ""
    base_name = choose_filename(metadata)
    mp3_path = unique_target(target_dir, base_name, "mp3")
    output_template = str(mp3_path.with_suffix(".%(ext)s"))
    command = ytdlp_base_command() + [
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--embed-metadata",
        "--embed-thumbnail",
        "--output",
        output_template,
        normalized,
    ]
    process = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    collected = []
    assert process.stdout is not None
    for line in process.stdout:
        text = line.strip()
        collected.append(text)
        if progress_callback and text:
            progress_callback(text)
    return_code = process.wait()
    if return_code != 0 or not mp3_path.exists():
        result = DownloadResult(
            url=normalized,
            status="failed",
            artist=artist,
            title=title,
            error="\n".join(line for line in collected[-12:] if line) or "yt-dlp download failed.",
        )
        append_history(result.to_history_entry(source_type, target_dir))
        return result

    result = DownloadResult(
        url=normalized,
        status="completed",
        artist=artist,
        title=title,
        output_path=str(mp3_path),
    )
    append_history(result.to_history_entry(source_type, target_dir))
    return result


def write_playlist_report(report_path: Path, rows: list[dict]) -> Path:
    import csv

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "track_number",
                "artist",
                "track_title",
                "soundcloud_url",
                "download_status",
                "output_filename",
                "error_message",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return report_path
