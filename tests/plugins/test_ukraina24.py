import unittest

from streamlink.plugins.kanalukraina import Ukraina24


class TestPluginUkraina24(unittest.TestCase):
    def test_can_handle_url(self):
        should_match = [
            'https://ukraina24.segodnya.ua/'
        ]
        for url in should_match:
            self.assertTrue(Ukraina24.can_handle_url(url))

    def test_can_handle_url_negative(self):
        should_not_match = [
            'https://video.oz/'
        ]
        for url in should_not_match:
            self.assertFalse(Ukraina24.can_handle_url(url))
