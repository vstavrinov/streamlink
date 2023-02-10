import unittest

from streamlink.plugins.ukraina24 import Ukraina24


class TestPluginUkraina24(unittest.TestCase):
    __plugin__ = Ukraina24

    should_match = [
        "https://ukraina24.segodnya.ua/online",
    ]

    should_not_match = [
        "https://ukraina24.segodnya.ua",
    ]
