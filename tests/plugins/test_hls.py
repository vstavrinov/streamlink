from unittest.mock import Mock, call

import pytest

from streamlink.plugin.plugin import LOW_PRIORITY, NO_PRIORITY, NORMAL_PRIORITY
from streamlink.plugins.hls import HLSPlugin
from streamlink.session import Streamlink
from streamlink.stream.hls import HLSStream
from tests.plugins import PluginCanHandleUrl


class TestPluginCanHandleUrlHLSPlugin(PluginCanHandleUrl):
    __plugin__ = HLSPlugin

    should_match = [
        "example.com/foo.m3u8",
        "http://example.com/foo.m3u8",
        "https://example.com/foo.m3u8",
        "hls://example.com/foo",
        "hls://http://example.com/foo",
        "hls://https://example.com/foo",
        "hlsvariant://example.com/foo",
        "hlsvariant://http://example.com/foo",
        "hlsvariant://https://example.com/foo",
    ]


@pytest.mark.parametrize(("url", "priority"), [
    ("http://example.com/foo.m3u8", LOW_PRIORITY),
    ("hls://http://example.com/foo.m3u8", NORMAL_PRIORITY),
    ("hls://http://example.com/bar", NORMAL_PRIORITY),
    ("hlsvariant://http://example.com/foo.m3u8", NORMAL_PRIORITY),
    ("hlsvariant://http://example.com/bar", NORMAL_PRIORITY),
    ("http://example.com/bar", NO_PRIORITY),
])
def test_priority(url, priority):
    assert next((matcher.priority for matcher in HLSPlugin.matchers if matcher.pattern.match(url)), NO_PRIORITY) == priority


@pytest.mark.parametrize(("url", "expected"), [
    ("example.com/foo.m3u8", "https://example.com/foo.m3u8"),
    ("http://example.com/foo.m3u8", "http://example.com/foo.m3u8"),
    ("https://example.com/foo.m3u8", "https://example.com/foo.m3u8"),
    ("hls://example.com/foo", "https://example.com/foo"),
    ("hls://http://example.com/foo", "http://example.com/foo"),
    ("hls://https://example.com/foo", "https://example.com/foo"),
    ("hlsvariant://example.com/foo", "https://example.com/foo"),
    ("hlsvariant://http://example.com/foo", "http://example.com/foo"),
    ("hlsvariant://https://example.com/foo", "https://example.com/foo"),
])
@pytest.mark.parametrize(("isvariant", "streams"), [
    (False, ["live"]),
    (True, ["720p", "1080p"]),
])
def test_get_streams(
    monkeypatch: pytest.MonkeyPatch,
    session: Streamlink,
    url: str,
    expected: str,
    isvariant: bool,
    streams: list,
):
    monkeypatch.setattr("streamlink.stream.hls.HLSStream.__init__", Mock(return_value=None))

    fakestreams = {}
    if isvariant:
        fakestreams["720p"] = HLSStream(session, url)
        fakestreams["1080p"] = HLSStream(session, url)

    mock_parse_variant_playlist = Mock(return_value=fakestreams)
    monkeypatch.setattr("streamlink.stream.hls.HLSStream.parse_variant_playlist", mock_parse_variant_playlist)

    plugin = HLSPlugin(session, url)
    result = plugin.streams()
    result.pop("worst", None)
    result.pop("best", None)

    assert list(result.keys()) == streams
    assert all(isinstance(s, HLSStream) for s in result.values())
    assert mock_parse_variant_playlist.call_args_list == [call(session, expected)]
