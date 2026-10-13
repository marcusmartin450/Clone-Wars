from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

from soundcloud_backend import (
    DownloadResult,
    first_non_empty,
    normalize_soundcloud_url,
    sanitize_filename_part,
    unique_target,
    ytdlp_base_command,
)


def youtube_fallback_query(url: str, track_info: dict | None = None) -> str:
    track_info = track_info or {}
    artist = first_non_empty(track_info.get("artist"))
    title = first_non_empty(track_info.get("title"), track_info.get("track"))
    if not artist or not title:
        parts = [part for part in urlparse(url).path.split("/") if part]
        if len(parts) >= 2:
            artist = artist or parts[-2].replace("-", " ")
            title = title or parts[-1].replace("-", " ")
    search_terms = " ".join(part for part in (artist, title) if part)
    return f"ytsearch1:{search_terms} audio" if search_terms else ""


def output_template_for_track(target_dir: Path, track_info: dict | None) -> str:
    track_info = track_info or {}
    artist = sanitize_filename_part(first_non_empty(track_info.get("artist")), "Unknown Artist")
    title = sanitize_filename_part(
        first_non_empty(track_info.get("title"), track_info.get("track")),
        "Unknown Track",
    )
    target = unique_target(target_dir, f"{artist} - {title}", "mp3")
    return str(target.with_suffix(".%(ext)s"))


def run_download(command: list[str], env: dict[str, str], progress_callback=None) -> tuple[int, list[str]]:
    process = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output_lines = []
    assert process.stdout is not None
    for line in process.stdout:
        message = line.strip()
        if message:
            output_lines.append(message)
            if progress_callback:
                progress_callback(message)
    return process.wait(), output_lines


def download_track_exact(
    url: str,
    env: dict[str, str],
    target_dir: Path,
    _source_type: str = "single",
    progress_callback=None,
    track_info: dict | None = None,
) -> DownloadResult:
    normalized = normalize_soundcloud_url(url)
    output_folder = Path(target_dir).expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)
    previous_files = {path: path.stat().st_mtime_ns for path in output_folder.glob("*.mp3")}
    output_template = str(output_folder / "%(artist,uploader)s - %(title)s.%(ext)s")
    common_options = [
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--embed-thumbnail",
        "--convert-thumbnails",
        "jpg",
        "--add-metadata",
        "--parse-metadata",
        "%(uploader)s:%(artist)s",
        "--postprocessor-args",
        "ffmpeg:-metadata genre=House",
        "--no-playlist",
    ]
    command = ytdlp_base_command() + common_options + [
        "-o",
        output_template,
        normalized,
    ]
    return_code, output_lines = run_download(command, env, progress_callback)

    changed_files = []
    for path in output_folder.glob("*.mp3"):
        previous_modified = previous_files.get(path)
        if previous_modified is None or path.stat().st_mtime_ns > previous_modified:
            changed_files.append(path)
    output_path = max(changed_files, key=lambda path: path.stat().st_mtime_ns) if changed_files else None

    if return_code == 0 and output_path is not None:
        return DownloadResult(
            url=normalized,
            status="completed",
            output_path=str(output_path),
        )

    fallback_query = youtube_fallback_query(normalized, track_info)
    if fallback_query:
        if progress_callback:
            progress_callback("SoundCloud download failed. Searching YouTube for an alternative source...")
        fallback_template = output_template_for_track(output_folder, track_info)
        fallback_command = ytdlp_base_command() + common_options + [
            "-o",
            fallback_template,
            fallback_query,
        ]
        fallback_code, fallback_output = run_download(fallback_command, env, progress_callback)
        fallback_path = Path(fallback_template.replace("%(ext)s", "mp3"))
        if fallback_code == 0 and fallback_path.exists():
            if progress_callback:
                progress_callback("YouTube fallback download completed.")
            return DownloadResult(
                url=normalized,
                status="completed",
                artist=first_non_empty((track_info or {}).get("artist")) or "",
                title=first_non_empty((track_info or {}).get("title")) or "",
                output_path=str(fallback_path),
                download_source="youtube",
            )
        soundcloud_error = "\n".join(output_lines[-6:]) or "SoundCloud download failed."
        youtube_error = "\n".join(fallback_output[-6:]) or "YouTube fallback failed."
        return DownloadResult(
            url=normalized,
            status="failed",
            error=f"SoundCloud failed:\n{soundcloud_error}\nYouTube fallback failed:\n{youtube_error}",
        )

    return DownloadResult(
        url=normalized,
        status="failed",
        error="\n".join(output_lines[-12:]) or "yt-dlp download failed.",
    )
