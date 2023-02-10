"""
$url kanalukraina.tv
$type live
"""

import logging
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import esprima  # type: ignore

from streamlink.plugin import Plugin, pluginmatcher
from streamlink.plugin.api import useragents
from streamlink.stream import HLSStream


log = logging.getLogger(__name__)


class HTML_Parser(HTMLParser):
    js = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = dict(attrs)
            if "type" in attrs and attrs["type"][25:] == "text/javascript":
                self.js = True

    def handle_data(self, data):
        if self.js and data.find("PLAYER_SETTINGS") > 0:
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
    r"https?://kanalukraina.tv/online",
))
class KanalUkraina(Plugin):

    def _get_streams(self):
        self.session.http.headers = {
            "Referer": self.url,
            "User-Agent": useragents.FIREFOX,
        }
        html = self.session.http.get(self.url).text
        if html:
            body = get_js(html)
        if body:
            for node in body:
                if node.expression:
                    if node.expression.arguments:
                        for item in node.expression.arguments:
                            if item.body.body:
                                for node in item.body.body:
                                    if node.expression.arguments:
                                        for item in node.expression.arguments:
                                            if item.properties:
                                                for kind in item.properties:
                                                    if kind.key:
                                                        if kind.key.name:
                                                            if kind.key.name == "url":
                                                                if urlsplit(kind.value.value).netloc:
                                                                    stream_url = kind.value.value
                                                                else:
                                                                    stream_url = urljoin(self.url, kind.value.value)
                                                                log.debug("Stream URL: {0}".format(stream_url))
                                                                yield "live", HLSStream(self.session, stream_url)
                                                                break


__plugin__ = KanalUkraina
