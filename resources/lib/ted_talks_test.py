import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

with patch.dict(sys.modules, {
    'xbmc': MagicMock(),
    'xbmcgui': MagicMock(),
    'xbmcplugin': MagicMock(),
    'xbmcvfs': MagicMock(),
}):
    from . import ted_talks


class TestPlayVideoSubtitles(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        ted_talks.xbmcgui.ListItem.reset_mock()
        ted_talks.xbmcplugin.setResolvedUrl.reset_mock()
        ted_talks.xbmcplugin.setResolvedUrl.side_effect = None
        self.ui = ted_talks.UI(MagicMock(), MagicMock())

    def play(self, subtitles, languages):
        self.ui.ted_talks.get_video_details.return_value = ('playlist', 'Talk', subtitles, {})
        with patch.object(ted_talks.settings, 'get_subtitle_languages', return_value=languages), \
                patch.object(ted_talks.xbmcvfs, 'translatePath', return_value=self.temp_dir.name), \
                patch.object(ted_talks.plugin, 'report'), \
                patch.object(ted_talks.sys, 'argv', ['plugin', '1']):
            self.ui.playVideo('https://www.ted.com/talks/example', None)

    def test_subtitles_are_attached_before_resolving_video(self):
        subtitle_file = os.path.join(self.temp_dir.name, 'ted_talks_subs.srt')
        list_item = ted_talks.xbmcgui.ListItem.return_value

        def on_resolve(handle, succeeded, item):
            self.assertEqual(1, handle)
            self.assertTrue(succeeded)
            self.assertIs(list_item, item)
            with open(subtitle_file, encoding='utf-8') as fh:
                self.assertEqual('1\n00:00:00,000 --> 00:00:01,000\nHello\n', fh.read())
            list_item.setSubtitles.assert_called_once_with([subtitle_file])

        with patch.object(ted_talks.xbmcplugin.setResolvedUrl, 'side_effect', on_resolve):
            self.play('1\n00:00:00,000 --> 00:00:01,000\nHello\n', ['en'])

        self.ui.ted_talks.get_video_details.assert_called_once_with(
            url='https://www.ted.com/talks/example', subs_language=['en'])

    def test_disabled_subtitles_do_not_attach_old_file(self):
        subtitle_file = os.path.join(self.temp_dir.name, 'ted_talks_subs.srt')
        with open(subtitle_file, 'w', encoding='utf-8') as fh:
            fh.write('Old subtitles')
        list_item = ted_talks.xbmcgui.ListItem.return_value

        self.play(None, None)

        self.ui.ted_talks.get_video_details.assert_called_once_with(
            url='https://www.ted.com/talks/example', subs_language=None)
        with open(subtitle_file, encoding='utf-8') as fh:
            self.assertEqual('', fh.read())
        list_item.setSubtitles.assert_not_called()

    def test_unavailable_subtitles_are_not_attached(self):
        self.play(None, ['de'])

        ted_talks.xbmcgui.ListItem.return_value.setSubtitles.assert_not_called()
