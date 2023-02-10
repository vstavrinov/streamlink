import unittest

from streamlink.plugins.kanalukraina import KanalUkraina


class TestPluginKanalUkraina(unittest.TestCase):
    __plugin__ = KanalUkraina

    should_match = [
        "https://kanalukraina.tv/online",
    ]

    should_not_match = [
        "https://kanalukraina.tv",
    ]
