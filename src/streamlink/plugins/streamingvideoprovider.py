import logging
import re
from time import time

from streamlink.plugin import Plugin, PluginError, pluginmatcher
from streamlink.plugin.api import validate
from streamlink.stream import HLSStream, RTMPStream

log = logging.getLogger(__name__)

SWF_URL = "http://play.streamingvideoprovider.com/player2.swf"
API_URL = "http://player.webvideocore.net/index.php"

_hls_re = re.compile(r"'(http://.+\.m3u8)'")

_rtmp_schema = validate.Schema(
    validate.xml_findtext("./info/url"),
    validate.url(scheme="rtmp")
)
_hls_schema = validate.Schema(
    validate.transform(_hls_re.search),
    validate.any(
        None,
        validate.all(
            validate.get(1),
            validate.url(
                scheme="http",
                path=validate.endswith("m3u8")
            )
        )
    )
)


@pluginmatcher(re.compile(
    r"https?://(\w+\.)?streamingvideoprovider\.co\.uk/(?P<channel>[^/&?]+)"
))
class Streamingvideoprovider(Plugin):
    def _get_hls_stream(self, channel_name):
        params = {
            "l": "info",
            "a": "ajax_video_info",
            "file": channel_name,
            "rid": time()
        }
        playlist_url = self.session.http.get(API_URL, params=params, schema=_hls_schema)
        if not playlist_url:
            return

        return HLSStream(self.session, playlist_url)

    def _get_rtmp_stream(self, channel_name):
        params = {
            "l": "info",
            "a": "xmlClipPath",
            "clip_id": channel_name,
            "rid": time()
        }
        res = self.session.http.get(API_URL, params=params)
        rtmp_url = self.session.http.xml(res, schema=_rtmp_schema)

        return RTMPStream(self.session, {
            "rtmp": rtmp_url,
            "swfVfy": SWF_URL,
            "live": True
        })

    def _get_streams(self):
        channel_name = self.match.group("channel")

        try:
            stream = self._get_rtmp_stream(channel_name)
            yield "live", stream
        except PluginError as err:
            log.error("Unable to extract RTMP stream: {0}".format(err))

        try:
            stream = self._get_hls_stream(channel_name)
            if stream:
                yield "live", stream
        except PluginError as err:
            log.error("Unable to extract HLS stream: {0}".format(err))


__plugin__ = Streamingvideoprovider
