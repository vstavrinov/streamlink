from html.parser import HTMLParser
import logging
import re

import esprima

from streamlink.plugin import Plugin
from streamlink.plugin.api import useragents
from streamlink.stream import HLSStream

log = logging.getLogger(__name__)
_url_re = re.compile(r'https?://ukraina24.segodnya.ua/online', re.VERBOSE)


class HTML_Parser(HTMLParser):
    js = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            attrs = dict(attrs)
            if 'type' in attrs and attrs['type'] == 'text/javascript':
                self.js = True

    def handle_data(self, data):
        if self.js and data.find('initPlayer') > 0:
            self.data = data


def get_js(html):
    parser = HTML_Parser()
    parser.feed(html)
    try:
        js = parser.data
    except Exception as exception:
        log.error('Exception {0}: {1}\n'.format(type(exception).__name__, exception))
        return False
    parsed = esprima.parseScript(js, {"tolerant": True})
    return parsed.body


class Ukraina24(Plugin):

    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _get_streams(self):
        self.session.http.headers = {
            "Referer": self.url,
            "User-Agent": useragents.FIREFOX
        }
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
                                                if item.key.name and item.key.name == 'source':
                                                    stream_url = item.value.value
                                                    log.debug("Stream URL: {0}".format(stream_url))
                                                    return HLSStream.parse_variant_playlist(self.session,
                                                                                            stream_url)


__plugin__ = Ukraina24
