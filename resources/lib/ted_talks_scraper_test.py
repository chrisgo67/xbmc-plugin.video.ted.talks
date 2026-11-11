import json
import unittest
from unittest.mock import MagicMock

from . import ted_talks_scraper


class TestTedTalks(unittest.TestCase):

    def setUp(self):
        self.logger = MagicMock()
        self.fetcher = MagicMock()
        self.sut = ted_talks_scraper.TedTalks(self.fetcher, self.logger)

    def test_resolve_playlist_urls(self):
        root = 'https://hls.ted.com'
        path = '/project_masters/1580/'
        for uri, expected in (
            (None, None),
            ('audio.m3u8', root + path + 'audio.m3u8'),
            ('/videos/audio.m3u8', root + '/videos/audio.m3u8'),
            ('https://example.com/audio.m3u8', 'https://example.com/audio.m3u8'),
        ):
            with self.subTest(uri=uri):
                self.assertEqual(expected, self.sut.__resolve__(root, path, uri))

    def test_process_playlist_with_in_band_audio(self):
        self.fetcher.get.return_value.url = 'https://hls.ted.com/project_masters/1580/manifest.m3u8'
        self.fetcher.get.return_value.text = (
            '#EXTM3U\n'
            '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="English",DEFAULT=YES\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=100000,AUDIO="audio"\n'
            'video.m3u8\n'
        )
        playlist = ted_talks_scraper.m3u8.loads(
            self.sut.__process_m3u8__('https://example.com/master.m3u8'))

        self.assertIsNone(playlist.media[0].uri)
        self.assertEqual(
            'https://hls.ted.com/project_masters/1580/video.m3u8',
            playlist.playlists[0].uri,
        )

    def assert_video_details(self, uri_prefix, expected_base):
        talk_url = 'https://www.ted.com/talks/example_talk'
        manifest_url = 'https://example.com/manifest.m3u8'
        video_data = {
            'title': 'Example talk',
            'description': 'Example description',
            'videoPlayerData': {
                'speaker': 'Example speaker',
                'resources': {'hls': {'stream': manifest_url + '?intro_master_id=2346'}},
            },
        }
        self.fetcher.get_HTML.return_value = (
            '<script id="__NEXT_DATA__" type="application/json">%s</script>' %
            json.dumps({'props': {'pageProps': {'videoData': video_data}}})
        )
        self.fetcher.get.return_value.url = (
            'https://hls.ted.com/project_masters/1580/manifest.m3u8'
        )
        self.fetcher.get.return_value.text = (
            '#EXTM3U\n'
            '#EXT-X-VERSION:4\n'
            '#EXT-X-INDEPENDENT-SEGMENTS\n'
            '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="English",'
            'DEFAULT=YES,AUTOSELECT=YES,URI="{prefix}audio.m3u8?track=en"\n'
            '#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",'
            'LANGUAGE="en",URI="{prefix}subtitles.m3u8"\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=100000,RESOLUTION=640x360,'
            'CODECS="avc1.42c01e,mp4a.40.2",AUDIO="audio",SUBTITLES="subs"\n'
            '{prefix}video.m3u8?quality=low\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=200000,RESOLUTION=1280x720,'
            'CODECS="avc1.640028,mp4a.40.2",AUDIO="audio",SUBTITLES="subs"\n'
            '{prefix}video.m3u8?quality=high\n'
            '#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=5000,RESOLUTION=640x360,'
            'CODECS="avc1.42c01e",URI="{prefix}iframe.m3u8?quality=low"\n'
        ).format(prefix=uri_prefix)

        playlist_text, title, subs, info = self.sut.get_video_details(talk_url)
        playlist = ted_talks_scraper.m3u8.loads(playlist_text)

        self.fetcher.get_HTML.assert_called_once_with(talk_url)
        self.fetcher.get.assert_called_once_with(manifest_url)
        self.assertEqual('Example talk', title)
        self.assertIsNone(subs)
        self.assertEqual({
            'Director': 'Example speaker', 'Genre': 'TED',
            'Plot': 'Example description', 'PlotOutline': 'Example description',
        }, info)
        self.assertEqual(4, playlist.version)
        self.assertTrue(playlist.is_independent_segments)
        self.assertEqual(1, len(playlist.media))
        audio = playlist.media[0]
        self.assertEqual('AUDIO', audio.type)
        self.assertEqual(expected_base + 'audio.m3u8?track=en', audio.uri)
        self.assertEqual('audio', audio.group_id)
        self.assertEqual('YES', audio.default)
        self.assertEqual('YES', audio.autoselect)
        self.assertEqual([
            expected_base + 'video.m3u8?quality=low',
            expected_base + 'video.m3u8?quality=high',
        ], [variant.uri for variant in playlist.playlists])
        self.assertEqual([100000, 200000], [
            variant.stream_info.bandwidth for variant in playlist.playlists])
        self.assertEqual([(640, 360), (1280, 720)], [
            variant.stream_info.resolution for variant in playlist.playlists])
        self.assertEqual(['avc1.42c01e,mp4a.40.2', 'avc1.640028,mp4a.40.2'], [
            variant.stream_info.codecs for variant in playlist.playlists])
        for variant in playlist.playlists:
            self.assertEqual('audio', variant.stream_info.audio)
            self.assertEqual(['AUDIO'], [media.type for media in variant.media])
            self.assertEqual(audio.uri, variant.media[0].uri)
        self.assertEqual(1, len(playlist.iframe_playlists))
        iframe = playlist.iframe_playlists[0]
        self.assertEqual(expected_base + 'iframe.m3u8?quality=low', iframe.uri)
        self.assertEqual(5000, iframe.iframe_stream_info.bandwidth)
        self.assertEqual((640, 360), iframe.iframe_stream_info.resolution)
        self.assertEqual('avc1.42c01e', iframe.iframe_stream_info.codecs)

    def test_smoke_relative_path(self):
        """Resolve relative URLs against the redirected manifest's directory."""
        self.assert_video_details('', 'https://hls.ted.com/project_masters/1580/')

    def test_smoke_full_path(self):
        """Resolve root-relative URLs against the redirected manifest's host."""
        self.assert_video_details('/videos/example/', 'https://hls.ted.com/videos/example/')
