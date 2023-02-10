"""
$url ukraina24.segodnya.ua
$type live
"""

import logging
import re
from html.parser import HTMLParser

import esprima  # type: ignore

from streamlink.plugin import Plugin, pluginmatcher
from streamlink.stream import HLSStream


log = logging.getLogger(__name__)


class HTML_Parser(HTMLParser):
    js = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = dict(attrs)
            if "type" in attrs and attrs["type"] == "text/javascript":
                self.js = True

    def handle_data(self, data):
        if self.js and data.find("initPlayer") > 0:
            self.data = data


def get_js(html):
    parser = HTML_Parser()
    parser.feed(html)
    try:
        js = parser.data
    except Exception as exception:
        log.error("Exception {0}: {1}\n".format(type(exception).__name__, exception))
        return False
    parsed = esprima.parseScript(js, {"tolerant": True})
    return parsed.body


@pluginmatcher(re.compile(
    r"https?://ukraina24.segodnya.ua/online",
))
class Ukraina24(Plugin):

    def _get_streams(self):
        self.session.http.headers = {
            "Referer": self.url,
            "User-Agent": "Mozilla",
        }
        # This cookie encodes the user agent above. Don't change them!
        self.session.http.cookies.set("STC", "a4f963d2c0680cb534f626ae56a4609d")
        html = self.session.http.get(self.url).text
        if html:
            body = get_js(html)
        if body:
            for item in body:
                if item.expression and item.expression.arguments:
                    for item in item.expression.arguments:
                        if item.body and item.body.body:
                            for item in item.body.body:
                                if item.expression and item.expression.arguments:
                                    for item in item.expression.arguments:
                                        if item.properties:
                                            for item in item.properties:
                                                if item.key.name and item.key.name == "source":
                                                    stream_url = item.value.value
                                                    log.debug("Stream URL: {0}".format(stream_url))
                                                    yield "live", HLSStream(self.session, stream_url)


__plugin__ = Ukraina24
