from soundcloud_easy_gui import classify_soundcloud_url, download_counts_message


def test_live_download_counts_message():
    assert download_counts_message(7, 33, 6, 0, 1) == (
        "Processed 7 of 33. Downloaded 6, skipped 0, failed 1."
    )


def test_track_url():
    assert classify_soundcloud_url("https://soundcloud.com/artist/track-name?share=1") == (
        "track",
        "https://soundcloud.com/artist/track-name",
    )


def test_playlist_url():
    assert classify_soundcloud_url("https://soundcloud.com/artist/sets/my-playlist") == (
        "playlist",
        "https://soundcloud.com/artist/sets/my-playlist",
    )


def test_profile_url():
    assert classify_soundcloud_url("https://soundcloud.com/artist") == (
        "profile",
        "https://soundcloud.com/artist",
    )


def test_likes_url():
    assert classify_soundcloud_url("https://soundcloud.com/artist/likes/") == (
        "profile",
        "https://soundcloud.com/artist/likes",
    )


def test_invalid_url():
    try:
        classify_soundcloud_url("https://example.com/not-soundcloud")
    except RuntimeError as exc:
        assert "SoundCloud" in str(exc)
    else:
        raise AssertionError("Invalid URL was accepted")
