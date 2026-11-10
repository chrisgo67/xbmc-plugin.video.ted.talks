import sys
import unittest
from unittest.mock import MagicMock, patch

with patch.dict(sys.modules, {
    'xbmc': MagicMock(),
    'xbmcgui': MagicMock(),
    'xbmcplugin': MagicMock(),
    'xbmcvfs': MagicMock(),
}):
    from . import ted_talks


class TestSorting(unittest.TestCase):

    def test_directory_sort_methods(self):
        ui = ted_talks.UI(MagicMock(), MagicMock())
        with patch.object(ted_talks, 'xbmcplugin') as kodi, \
                patch.object(ted_talks.sys, 'argv', ['plugin', '1']):
            for method, expected in [
                ('title', kodi.SORT_METHOD_LABEL),
                ('date', kodi.SORT_METHOD_DATE),
                ('none', kodi.SORT_METHOD_NONE),
            ]:
                with self.subTest(method=method):
                    kodi.reset_mock()
                    ui.endofdirectory(sortMethod=method)
                    kodi.addSortMethod.assert_called_once_with(1, expected)
                    kodi.endOfDirectory.assert_called_once_with(handle=1, updateListing=False)

    def test_newest_talks_use_kodi_date_sorting(self):
        ui = ted_talks.UI(MagicMock(), MagicMock())
        with patch.object(ted_talks, 'NewTalksRss') as rss, \
                patch.object(ted_talks, 'xbmcplugin') as kodi, \
                patch.object(ted_talks, 'xbmc') as xbmc, \
                patch.object(ted_talks.sys, 'argv', ['plugin', '1']):
            rss.return_value.get_new_talks.return_value = []

            ui.newTalksRss()

            kodi.setContent.assert_called_once_with(1, 'videos')
            kodi.addSortMethod.assert_called_once_with(1, kodi.SORT_METHOD_DATE)
            kodi.endOfDirectory.assert_called_once_with(handle=1, updateListing=False)
            xbmc.executebuiltin.assert_not_called()
