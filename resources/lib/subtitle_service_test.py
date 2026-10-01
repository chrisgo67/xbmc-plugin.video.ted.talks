import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

xbmc = types.ModuleType('xbmc')
xbmc.Player = type('Player', (), {})
xbmcaddon = types.ModuleType('xbmcaddon')
xbmcaddon.Addon = MagicMock()
xbmcvfs = types.ModuleType('xbmcvfs')
xbmcvfs.translatePath = MagicMock()
with patch.dict(sys.modules, {'xbmc': xbmc, 'xbmcaddon': xbmcaddon, 'xbmcvfs': xbmcvfs}):
    from . import subtitle_service


class TestTedSubtitlePlayer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.player = subtitle_service.TedSubtitlePlayer()
        self.player.getPlayingFile = MagicMock(
            return_value=os.path.join(self.temp_dir.name, 'ted_talks.m3u8'))
        self.player.setSubtitles = MagicMock()
        self.player.showSubtitles = MagicMock()
        self.subs_file = os.path.join(self.temp_dir.name, 'ted_talks_subs.srt')
        with open(self.subs_file, 'w', encoding='utf-8') as fh:
            fh.write('1\n00:00:00,000 --> 00:00:01,000\nHello\n')
        subtitle_service.xbmcvfs.translatePath.return_value = self.temp_dir.name
        subtitle_service.xbmcaddon.Addon.return_value.getSetting.return_value = 'true'
        subtitle_service.xbmcaddon.Addon.reset_mock()

    def test_enables_subtitles_for_ted_even_when_kodi_default_is_off(self):
        self.player.onAVStarted()

        subtitle_service.xbmcaddon.Addon.assert_called_once_with(id='plugin.video.ted.talks')
        self.player.setSubtitles.assert_called_once_with(self.subs_file)
        self.player.showSubtitles.assert_called_once_with(True)

    def test_other_video_is_not_affected(self):
        self.player.getPlayingFile.return_value = os.path.join(self.temp_dir.name, 'other.m3u8')

        self.player.onAVStarted()

        subtitle_service.xbmcaddon.Addon.assert_not_called()
        self.player.setSubtitles.assert_not_called()
        self.player.showSubtitles.assert_not_called()

    def test_disabled_addon_setting_does_not_override_kodi(self):
        subtitle_service.xbmcaddon.Addon.return_value.getSetting.return_value = 'false'

        self.player.onAVStarted()

        self.player.setSubtitles.assert_not_called()
        self.player.showSubtitles.assert_not_called()

    def test_missing_or_empty_subtitles_are_not_enabled(self):
        for contents in (None, ''):
            with self.subTest(contents=contents):
                if contents is None:
                    os.remove(self.subs_file)
                else:
                    with open(self.subs_file, 'w', encoding='utf-8') as fh:
                        fh.write(contents)
                self.player.onAVStarted()
                self.player.setSubtitles.assert_not_called()
                self.player.showSubtitles.assert_not_called()
