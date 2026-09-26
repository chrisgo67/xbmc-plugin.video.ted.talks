import sys
import unittest

from unittest.mock import MagicMock

sys.modules.setdefault('xbmc', MagicMock())  # talk_scraper logs via xbmc.

from . import talk_scraper
from .subtitles_scraper import Subtitles
from .test_util import CachedHTMLProvider

class TestSubtitlesScraper(unittest.TestCase):

    def setUp(self):
        self.logger = MagicMock()
        self.fetcher = CachedHTMLProvider()
        self.sut = Subtitles(self.fetcher, self.logger)

    def tearDown(self):
        self.logger.assert_not_called()

    def test_format_time(self):
        self.assertEqual('00:00:00,000', self.sut.__format_time__(0))
        self.assertEqual('03:25:45,678', self.sut.__format_time__(12345678))

    def test_parse_time(self):
        self.assertEqual(5803, self.sut.__parse_time__('00:00:05.803'))
        self.assertEqual(12345678, self.sut.__parse_time__('03:25:45.678'))
        self.assertEqual(65432, self.sut.__parse_time__('01:05.432'))

    def test_vtt_to_srt(self):
        vtt = '''WEBVTT
Kind: captions

NOTE a comment

00:00:05.803 --> 00:00:08.421
Guten Morgen. Wie geht es Ihnen?

cue-2
00:08.421 --> 00:09.833 align:start position:10%
(Lachen)
Zweite Zeile

00:00:10.000 --> 00:00:11.000

'''
        self.assertEqual('''1
00:00:05,803 --> 00:00:08,421
Guten Morgen. Wie geht es Ihnen?

2
00:00:08,421 --> 00:00:09,833
(Lachen)
Zweite Zeile

''', self.sut.__vtt_to_srt__(vtt))

    def test_vtt_to_srt_empty(self):
        self.assertEqual('', self.sut.__vtt_to_srt__('WEBVTT\n\n'))

    def test_get_subtitles_for_talk(self):
        player_json = self.__get_player_json__('https://www.ted.com/talks/ken_robinson_do_schools_kill_creativity')
        subs = self.sut.get_subtitles_for_talk(player_json, ['banana', 'de', 'en'])
        # Timed for the stream without intro (talk_scraper removes it).
        self.assertTrue(subs.startswith('1\n00:00:02,299 --> 00:00:04,917\nGuten Morgen. Wie geht es Ihnen?\n'), subs[:100])

    def test_get_subtitles_for_talk_regional_variant(self):
        player_json = self.__get_player_json__('https://www.ted.com/talks/ken_robinson_do_schools_kill_creativity')
        subs = self.sut.get_subtitles_for_talk(player_json, ['pt-br', 'pt'])
        self.assertIn('Bom dia', subs)

    def test_get_subtitles_for_talk_no_match(self):
        player_json = self.__get_player_json__('https://www.ted.com/talks/ken_robinson_do_schools_kill_creativity')
        self.assertIsNone(self.sut.get_subtitles_for_talk(player_json, ['banana']))
        self.logger.assert_called_once()
        self.logger.reset_mock()

    def __get_player_json__(self, url):
        html = self.fetcher.get_HTML(url)
        return talk_scraper.get_talk(html, self.logger)[5]
