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


@pluginmatcher(
        re.compile(
            r"https?://ukraina24.segodnya.ua/online",
       )
)
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
            for item1 in body:
                if item1.expression and item1.expression.arguments:
                    for item2 in item1.expression.arguments:
                        if item2.body and item2.body.body:
                            for item3 in item2.body.body:
                                if item3.expression and item3.expression.arguments:
                                    for item4 in item3.expression.arguments:
                                        if item4.properties:
                                            for item5 in item4.properties:
                                                if item5.key.name and item5.key.name == "source":
                                                    stream_url = item5.value.value
                                                    log.debug("Stream URL: {0}".format(stream_url))
                                                    yield "live", HLSStream(self.session, stream_url)


__plugin__ = Ukraina24
