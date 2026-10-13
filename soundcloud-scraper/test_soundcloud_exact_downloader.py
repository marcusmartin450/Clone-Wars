from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import soundcloud_exact_downloader as downloader
from soundcloud_backend import track_summary_from_url


class FakeProcess:
    def __init__(self, lines, return_code, on_wait=None):
        self.stdout = iter(lines)
        self.return_code = return_code
        self.on_wait = on_wait

    def wait(self):
        if self.on_wait:
            self.on_wait()
        return self.return_code


class YouTubeFallbackTests(TestCase):
    def test_url_summary_keeps_drm_track_downloadable(self):
        summary = track_summary_from_url("https://soundcloud.com/mellizos/my-life-is-a-disco-in-the-mix")
        self.assertEqual(summary["artist"], "Mellizos")
        self.assertEqual(summary["title"], "My Life Is A Disco In The Mix")

    def test_query_uses_scraped_artist_and_title(self):
        query = downloader.youtube_fallback_query(
            "https://soundcloud.com/example/my-life-is-a-disco",
            {"artist": "Example Artist", "title": "My Life Is A Disco (In The Mix)"},
        )
        self.assertEqual(query, "ytsearch1:Example Artist My Life Is A Disco (In The Mix) audio")

    def test_failed_soundcloud_download_uses_youtube_fallback(self):
        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            track_info = {"artist": "Example Artist", "title": "My Life Is A Disco (In The Mix)"}
            expected_file = target_dir / "Example Artist - My Life Is A Disco (In The Mix).mp3"
            processes = [
                FakeProcess(["ERROR: SoundCloud format unavailable\n"], 1),
                FakeProcess(["[download] 100%\n"], 0, lambda: expected_file.touch()),
            ]

            with patch.object(downloader, "ytdlp_base_command", return_value=["python", "-m", "yt_dlp"]), patch.object(
                downloader.subprocess,
                "Popen",
                side_effect=processes,
            ) as popen:
                result = downloader.download_track_exact(
                    "https://soundcloud.com/example/my-life-is-a-disco",
                    {},
                    target_dir,
                    track_info=track_info,
                )

            self.assertEqual(result.status, "completed")
            self.assertEqual(result.download_source, "youtube")
            self.assertEqual(result.output_path, str(expected_file))
            self.assertEqual(popen.call_count, 2)
            self.assertTrue(popen.call_args_list[1].args[0][-1].startswith("ytsearch1:"))
