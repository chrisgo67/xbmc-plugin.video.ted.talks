import json
import timeit
import unittest

from . import talk_scraper


class TestTalkScraper(unittest.TestCase):

    def setUp(self):
        self.video_url = 'https://hls.ted.com/project_masters/1580/manifest.m3u8'
        self.player_json = {
            'title': 'Player title',
            'speaker': 'Ariel Garten',
            'resources': {
                'hls': {'stream': self.video_url + '?intro_master_id=2346'},
            },
        }
        self.talk_json = {
            'title': 'Know thyself, with a brain scanner',
            'presenterDisplayName': 'Presenter fallback',
            'description': 'A talk about the brain.',
        }

    def make_html(self, player_field, player_data):
        video_data = dict(self.talk_json, **{player_field: player_data})
        return '<script id="__NEXT_DATA__" type="application/json">%s</script>' % json.dumps({
            'props': {'pageProps': {'videoData': video_data}},
        })

    def test_get_ted_video(self):
        for field, player_data in (
            ('videoPlayerData', self.player_json),
            ('playerData', json.dumps(self.player_json)),
            ('playerData', self.player_json),
        ):
            with self.subTest(player_field=field, encoded=isinstance(player_data, str)):
                html = self.make_html(field, player_data)
                url, title, speaker, plot, talk_json, player_json = talk_scraper.get_talk(html)

                self.assertEqual(self.video_url, url)
                self.assertEqual(self.talk_json['title'], title)
                self.assertEqual(self.player_json['speaker'], speaker)
                self.assertEqual(self.talk_json['description'], plot)
                self.assertEqual(dict(self.talk_json, **{field: player_data}), talk_json)
                self.assertEqual(self.player_json, player_json)

    def test_get_ted_video_uses_title_and_speaker_fallbacks(self):
        self.talk_json.pop('title')
        self.player_json.pop('speaker')
        html = self.make_html('videoPlayerData', self.player_json)

        _, title, speaker, _, _, _ = talk_scraper.get_talk(html)

        self.assertEqual(self.player_json['title'], title)
        self.assertEqual(self.talk_json['presenterDisplayName'], speaker)

    def test_performance(self):
        html = self.make_html('videoPlayerData', self.player_json)
        timer = timeit.Timer(lambda: talk_scraper.get_talk(html))
        repeats = 10
        elapsed = timer.timeit(repeats)
        self.assertLess(elapsed, 4)
