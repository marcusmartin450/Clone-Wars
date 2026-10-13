from soundcloud_easy_gui import classify_soundcloud_url


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
