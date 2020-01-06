import re
import logging
from html.parser import HTMLParser
from streamlink.plugin import Plugin
from streamlink.plugin.api import useragents
from streamlink.stream import HLSStream
import esprima
import jsbeautifier

log = logging.getLogger(__name__)
_url_re = re.compile(r'https?://(www\.)?arconaitv\.us/stream\.php\?id=((\d+)|(random))')


class HTML_Parser(HTMLParser):
    js = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.js = True

    def handle_data(self, data):
        if self.js and data.find("document.getElementsByTagName('video')") > 0:
            self.data = data


def get_js(html):
    parser = HTML_Parser()
    parser.feed(html)
    try:
        js = parser.data
    except Exception as exception:
        log.error('Exception {0}: {1}\n'.format(type(exception).__name__, exception))
        return False

    beauty = jsbeautifier.beautify(js).replace('\\', '')
    parsed = esprima.parseScript(beauty, {"tolerant": True})
    return parsed.body


class ArconaiTv(Plugin):
    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def _get_streams(self):
        headers = {
            'User-Agent': useragents.CHROME,
            'Referer': self.url
        }

        response = self.session.http.get(self.url, headers=headers)
        text = response.text
        body = get_js(text)
        if body:
            for node in body:
                if node.expression:
                    if node.expression.callee:
                        if node.expression.callee:
                            if node.expression.callee.object:
                                if node.expression.callee.object.name:
                                    if node.expression.callee.object.name == 'pp':
                                        if node.expression.callee.property:
                                            if node.expression.callee.property.name:
                                                if node.expression.callee.property.name == 'src':
                                                    if node.expression.arguments:
                                                        for unit in node.expression.arguments:
                                                            if unit.properties:
                                                                for item in unit.properties:
                                                                    if item.key:
                                                                        if item.key.name:
                                                                            if item.key.name == 'src':
                                                                                if item.value:
                                                                                    if item.value.value:
                                                                                        url = item.value.value
                                                                                        break

        self.logger.debug('HLS URL: {0}'.format(url))
        yield 'live', HLSStream(self.session, url, headers=headers)


__plugin__ = ArconaiTv
