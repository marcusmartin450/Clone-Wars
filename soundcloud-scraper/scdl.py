#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
DOWNLOADS_DIR = Path.home() / "Downloads"
COMMON_BIN_DIRS = ["/usr/local/bin", "/opt/homebrew/bin"]
BUNDLED_YTDLP_DIR = PROJECT_DIR / "yt_dlp"
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")
DOWNLOAD_MODES = ("mp3", "best", "both")


def fail(message: str, details: str | None = None, exit_code: int = 1) -> int:
    print(f"Error: {message}", file=sys.stderr)
    if details:
        print(details.strip(), file=sys.stderr)
    return exit_code


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
    if not VENV_PYTHON.exists():
        if importlib.util.find_spec("yt_dlp") is not None:
            return [sys.executable, "-m", "yt_dlp"]
        raise RuntimeError(
            "yt-dlp is not available. Install it in the project virtualenv or bundle it with the app."
        )
    return [str(VENV_PYTHON), "-m", "yt_dlp"]


def ensure_dependencies(env: dict[str, str]) -> None:
    if shutil.which("ffmpeg", path=env["PATH"]) is None:
        raise RuntimeError(
            "FFmpeg is not available on PATH. Install FFmpeg or update the PATH in scdl.sh."
        )


def sanitize_filename_part(value: str | None, fallback: str) -> str:
    text = (value or "").strip()
    text = INVALID_FILENAME_CHARS.sub(" ", text)
    text = WHITESPACE.sub(" ", text).strip(" .")
    return text or fallback


def sanitize_folder_name(value: str | None) -> str | None:
    if value is None:
        return None
    return sanitize_filename_part(value, "")


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


def parse_url_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    pieces = re.split(r"[\r\n,]+", raw_value)
    return [piece.strip() for piece in pieces if piece.strip()]


def resolve_target_dir(folder_name: str | None, target_dir_value: str | None) -> Path:
    if target_dir_value:
        target_dir = Path(target_dir_value).expanduser()
        if not target_dir.is_absolute():
            raise RuntimeError("Please provide an absolute folder path for --target-dir.")
        return target_dir
    if folder_name is None:
        return DOWNLOADS_DIR
    clean_name = sanitize_folder_name(folder_name)
    if not clean_name:
        raise RuntimeError("Please provide a valid folder name.")
    return DOWNLOADS_DIR / clean_name


def fetch_metadata(url: str, env: dict[str, str]) -> dict[str, object]:
    command = ytdlp_base_command() + ["--dump-single-json", "--skip-download", url]
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "yt-dlp metadata lookup failed.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"yt-dlp returned invalid metadata JSON: {exc}") from exc


def download_track(url: str, env: dict[str, str], target_dir: Path, mode: str) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    metadata = fetch_metadata(url, env)
    base_name = choose_filename(metadata)
    mp3_path = unique_target(target_dir, base_name, "mp3")
    mp3_template = str(mp3_path.with_suffix(".%(ext)s"))
    mp3_command = ytdlp_base_command() + [
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--embed-metadata",
        "--embed-thumbnail",
        "--output",
        mp3_template,
        url,
    ]
    result = subprocess.run(mp3_command, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "yt-dlp MP3 download failed."
        raise RuntimeError(details)
    if not mp3_path.exists():
        raise RuntimeError(f"Download finished but the expected MP3 file was not found at {mp3_path}")
    return [mp3_path]


def open_in_finder(path: Path, env: dict[str, str]) -> None:
    result = subprocess.run(
        [
            "/usr/bin/osascript",
            "-e",
            'on run argv',
            "-e",
            'set targetPath to POSIX file (item 1 of argv)',
            "-e",
            'tell application "Finder"',
            "-e",
            'activate',
            "-e",
            'open targetPath',
            "-e",
            'end tell',
            "-e",
            'end run',
            str(path),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Could not open {path} in Finder.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scdl",
        description="Download one or more SoundCloud tracks as MP3 files into Downloads.",
    )
    parser.add_argument("urls", nargs="*", help='One or more SoundCloud URLs, each kept in quotes when needed.')
    parser.add_argument("--folder", help="Optional folder name to create inside Downloads.")
    parser.add_argument("--target-dir", help="Optional absolute path to an existing folder or a folder to create.")
    parser.add_argument(
        "--format",
        choices=DOWNLOAD_MODES,
        default="mp3",
        help="Choose MP3, best original audio, or both. Default: mp3",
    )
    parser.add_argument(
        "--open-folder",
        action="store_true",
        help="Open the destination folder in Finder after any successful downloads.",
    )
    parser.add_argument(
        "--url-list",
        help="A comma-separated or newline-separated list of SoundCloud URLs.",
    )
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    urls = [url.strip() for url in args.urls if url.strip()]
    urls.extend(parse_url_list(args.url_list))

    if not urls:
        return fail('Usage: scdl "SOUNDCLOUD_URL" or scdl --folder "Folder Name" "URL1" "URL2"')

    env = build_env()

    try:
        ensure_dependencies(env)
        target_dir = resolve_target_dir(args.folder, args.target_dir)
    except RuntimeError as exc:
        return fail(str(exc))

    target_dir_existed_before = target_dir.exists()

    successes: list[Path] = []
    failures: list[tuple[str, str]] = []

    for url in urls:
        try:
            successes.extend(download_track(url, env, target_dir, args.format))
        except RuntimeError as exc:
            failures.append((url, str(exc)))

    if args.open_folder and successes:
        try:
            open_in_finder(target_dir, env)
        except RuntimeError as exc:
            failures.append((str(target_dir), f"Downloaded files but could not open Finder: {exc}"))

    if not failures:
        if len(successes) == 1:
            print(f"Success: saved file to {successes[0]}")
        else:
            print(f"Success: saved {len(successes)} files to {target_dir}")
            for saved_file in successes:
                print(f"- {saved_file}")
        return 0

    if not successes and not target_dir_existed_before and target_dir.exists() and not any(target_dir.iterdir()):
        target_dir.rmdir()

    if successes:
        print(f"Completed with some errors: saved {len(successes)} files to {target_dir}", file=sys.stderr)
        for saved_file in successes:
            print(f"- saved: {saved_file}", file=sys.stderr)
    for failed_item, message in failures:
        print(f"- {failed_item}: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
