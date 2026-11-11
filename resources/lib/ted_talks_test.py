import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

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
        self.xbmcgui = MagicMock()
        self.xbmcplugin = MagicMock()
        self.xbmcvfs = MagicMock()
        self.xbmcvfs.translatePath.return_value = self.temp_dir.name
        kodi_modules = patch.multiple(
            ted_talks, xbmcgui=self.xbmcgui, xbmcplugin=self.xbmcplugin,
            xbmcvfs=self.xbmcvfs)
        kodi_modules.start()
        self.addCleanup(kodi_modules.stop)
        self.ui = ted_talks.UI(MagicMock(), MagicMock())

    def play(self, subtitles, languages):
        self.ui.ted_talks.get_video_details.return_value = ('playlist', 'Talk', subtitles, {})
        with patch.object(ted_talks.settings, 'get_subtitle_languages', return_value=languages), \
                patch.object(ted_talks.plugin, 'report'), \
                patch.object(ted_talks.sys, 'argv', ['plugin', '1']):
            self.ui.playVideo('https://www.ted.com/talks/example', None)

    def test_subtitles_are_attached_before_resolving_video(self):
        subtitle_file = os.path.join(self.temp_dir.name, 'ted_talks_subs.srt')
        list_item = self.xbmcgui.ListItem.return_value

        def on_resolve(handle, succeeded, item):
            self.assertEqual(1, handle)
            self.assertTrue(succeeded)
            self.assertIs(list_item, item)
            with open(subtitle_file, encoding='utf-8') as fh:
                self.assertEqual('1\n00:00:00,000 --> 00:00:01,000\nHello\n', fh.read())
            list_item.setSubtitles.assert_called_once_with([subtitle_file])

        with patch.multiple(self.xbmcplugin, setResolvedUrl=MagicMock(side_effect=on_resolve)):
            self.play('1\n00:00:00,000 --> 00:00:01,000\nHello\n', ['en'])

        self.ui.ted_talks.get_video_details.assert_called_once_with(
            url='https://www.ted.com/talks/example', subs_language=['en'])

    def test_disabled_subtitles_do_not_attach_old_file(self):
        subtitle_file = os.path.join(self.temp_dir.name, 'ted_talks_subs.srt')
        with open(subtitle_file, 'w', encoding='utf-8') as fh:
            fh.write('Old subtitles')
        list_item = self.xbmcgui.ListItem.return_value

        self.play(None, None)

        self.ui.ted_talks.get_video_details.assert_called_once_with(
            url='https://www.ted.com/talks/example', subs_language=None)
        with open(subtitle_file, encoding='utf-8') as fh:
            self.assertEqual('', fh.read())
        list_item.setSubtitles.assert_not_called()

    def test_unavailable_subtitles_are_not_attached(self):
        self.play(None, ['de'])

        self.xbmcgui.ListItem.return_value.setSubtitles.assert_not_called()


class TestSpeakerNavigation(unittest.TestCase):

    def setUp(self):
        self.ui = MagicMock()
        self.logger = MagicMock()
        self.directory = MagicMock()
        self.entries = [
            self.speaker('zoe', 'M\u00fcller', 'Zoe'),
            self.speaker('anna', 'Muller', 'Anna'),
            self.speaker('aaker', 'Aaker', 'Jennifer'),
            self.speaker('other', '\u674e', '\u660e'),
        ]
        self.directory.read_cache.return_value = {'speakers': self.entries}
        self.directory.is_fresh.return_value = True
        self.gui = MagicMock()
        self.gui.DialogProgress.return_value.iscanceled.return_value = False
        self.directory_factory = MagicMock(return_value=self.directory)
        patches = [
            patch.multiple(
                ted_talks, SpeakerDirectory=self.directory_factory,
                xbmcgui=self.gui, xbmcplugin=MagicMock()),
            patch.object(ted_talks.sys, 'argv', ['plugin', '1']),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def speaker(slug, surname, first):
        return {
            'slug': slug, 'lastName': surname, 'firstName': first, 'middleName': '',
            'fullName': first + ' ' + surname, 'avatar': 'https://example.com/avatar.jpg',
        }

    def action(self, action_type):
        return action_type(self.ui, logger=self.logger, post_JSON=MagicMock())

    def test_speakers_show_letter_groups_without_fetching_fresh_index(self):
        self.action(ted_talks.SpeakersAction).run({})

        calls = self.ui.addItem.call_args_list
        self.assertEqual(['A', 'M', 'Other'], [call.args[0] for call in calls[:-1]])
        self.assertEqual(['A', 'M', '#'], [call.kwargs['args']['letter'] for call in calls[:-1]])
        self.assertEqual('speakerRefresh', calls[-1].args[1])
        self.directory.refresh.assert_not_called()
        self.gui.DialogProgress.assert_not_called()
        self.ui.endofdirectory.assert_called_once_with(sortMethod='none', updateListing=False)

    def test_main_registers_new_speaker_routes(self):
        self.directory.refresh.return_value = self.entries
        fetcher = MagicMock()
        with patch.multiple(ted_talks, UI=MagicMock(return_value=self.ui), Fetcher=fetcher):
            for arguments in (
                    {'mode': 'speakers'},
                    {'mode': 'speakerLetter', 'letter': 'A'},
                    {'mode': 'speakerRefresh'}):
                with self.subTest(arguments=arguments):
                    self.ui.reset_mock()
                    ted_talks.Main(arguments).run()
                    self.ui.addItem.assert_called()
                    self.ui.endofdirectory.assert_called_once()
            self.directory.refresh.assert_called_once()
            self.assertIs(fetcher.return_value.post_JSON,
                          self.directory_factory.call_args.args[0])

    def test_letter_preserves_surname_order_and_links(self):
        self.action(ted_talks.SpeakerLetterAction).run({'letter': 'M'})

        calls = self.ui.addItem.call_args_list
        self.assertEqual(['Muller, Anna', 'M\u00fcller, Zoe'], [call.args[0] for call in calls])
        self.assertEqual([
            'https://www.ted.com/speakers/anna', 'https://www.ted.com/speakers/zoe',
        ], [call.args[2] for call in calls])
        self.assertTrue(all(call.kwargs['img'] for call in calls))
        self.ui.endofdirectory.assert_called_once_with(sortMethod='none')

    def test_manual_refresh_forces_update_and_replaces_listing(self):
        self.directory.refresh.return_value = [self.entries[2]]
        self.action(ted_talks.SpeakerRefreshAction).run({})

        self.directory.refresh.assert_called_once()
        self.gui.DialogProgress.return_value.close.assert_called_once()
        self.ui.endofdirectory.assert_called_once_with(sortMethod='none', updateListing=True)

    def test_expired_index_refreshes_and_progress_can_be_cancelled(self):
        self.directory.is_fresh.return_value = False
        self.directory.refresh.side_effect = ted_talks.DirectoryCancelled()
        self.action(ted_talks.SpeakersAction).run({})

        update = self.directory.refresh.call_args.args[0]
        self.assertTrue(update(1, 2))
        self.gui.DialogProgress.return_value.update.assert_called_with(50, '1 / 2')
        self.gui.DialogProgress.return_value.iscanceled.return_value = True
        self.assertFalse(update(1, 2))
        self.assertEqual('A', self.ui.addItem.call_args_list[0].args[0])
        self.logger.assert_not_called()

    def test_failed_refresh_notifies_and_preserves_old_entries(self):
        self.directory.refresh.side_effect = requests.HTTPError('Service unavailable')
        self.action(ted_talks.SpeakerRefreshAction).run({})

        self.logger.assert_called_once()
        self.assertIn('Service unavailable', self.logger.call_args.args[0])
        self.assertTrue(self.logger.call_args.kwargs['friendly_message'])
        self.assertEqual(4, self.ui.addItem.call_count)
        self.gui.DialogProgress.return_value.close.assert_called_once()

    def test_first_build_cancellation_leaves_retry_available(self):
        self.directory.read_cache.return_value = None
        self.directory.is_fresh.return_value = False
        self.directory.refresh.side_effect = ted_talks.DirectoryCancelled()
        self.action(ted_talks.SpeakersAction).run({})

        self.ui.addItem.assert_called_once_with('Refresh speaker index', 'speakerRefresh')
        self.logger.assert_not_called()
        self.gui.DialogProgress.return_value.close.assert_called_once()

    def test_invalid_letter_is_reported_without_loading_index(self):
        self.action(ted_talks.SpeakerLetterAction).run({'letter': 'invalid'})

        self.logger.assert_called_once()
        self.directory.read_cache.assert_not_called()

    def test_legacy_page_group_still_opens(self):
        speakers = MagicMock()
        with patch.multiple(ted_talks, Speakers=speakers):
            speakers.return_value.get_speakers_for_pages.return_value = iter([
                4, ('Jennifer Aaker', 'https://www.ted.com/speakers/jennifer_aaker', 'avatar'),
            ])
            action = ted_talks.SpeakerGroupAction(
                self.ui, get_HTML=MagicMock(), logger=self.logger)
            action.run({'url': '1-4'})

        speakers.return_value.get_speakers_for_pages.assert_called_once_with([1, 2, 3, 4])
        self.assertEqual('speakerVids', self.ui.addItem.call_args.args[1])
