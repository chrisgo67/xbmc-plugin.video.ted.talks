import unittest
from . import settings

__saved_attributes__ = ['enable_subtitles', 'subtitle_fallback_english', 'xbmc_language', 'xbmc_language_code', 'kodi_subtitle_language', 'subtitle_language']

class TestSettings(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.saved = dict((a, getattr(settings, a)) for a in __saved_attributes__)
        settings.enable_subtitles = 'true'
        settings.subtitle_fallback_english = 'false'
        settings.xbmc_language = 'English'
        settings.xbmc_language_code = ''
        settings.kodi_subtitle_language = ''
        settings.subtitle_language = ''

    def tearDown(self):
        for a, v in self.saved.items():
            setattr(settings, a, v)
        unittest.TestCase.tearDown(self)

    def test_get_subtitle_languages_disabled(self):
        settings.enable_subtitles = 'false'
        self.assertIsNone(settings.get_subtitle_languages())

    def test_get_subtitle_languages_enabled_standard(self):
        settings.xbmc_language = 'Portuguese'
        self.assertEqual(['pt', 'pt-br'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_enabled_standard_nomatch(self):
        settings.xbmc_language = 'Klingon'
        self.assertEqual(None, settings.get_subtitle_languages())

    def test_get_subtitle_languages_enabled_custom(self):
        settings.subtitle_language = 'en,de , nl ,'
        self.assertEqual(['en', 'de', 'nl'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_custom_expands_variants(self):
        settings.subtitle_language = 'zh,pt-BR'
        self.assertEqual(['zh-cn', 'zh-tw', 'pt-br', 'pt'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_ui_code_with_region(self):
        settings.xbmc_language = 'Portuguese (Brazil)'
        settings.xbmc_language_code = 'pt-BR'
        self.assertEqual(['pt-br', 'pt'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_kodi_subtitle_setting_preferred(self):
        settings.xbmc_language_code = 'de-DE'
        settings.kodi_subtitle_language = 'French'
        self.assertEqual(['fr', 'fr-ca'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_kodi_subtitle_setting_special(self):
        settings.xbmc_language_code = 'de-DE'
        for value in ['original', 'default', 'none', 'forced_only']:
            settings.kodi_subtitle_language = value
            self.assertEqual(['de-de', 'de'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_custom_overrides_kodi(self):
        settings.xbmc_language_code = 'de-DE'
        settings.kodi_subtitle_language = 'French'
        settings.subtitle_language = 'nl'
        self.assertEqual(['nl'], settings.get_subtitle_languages())

    def test_get_subtitle_languages_fallback_english(self):
        settings.subtitle_fallback_english = 'true'
        settings.xbmc_language_code = 'de-DE'
        self.assertEqual(['de-de', 'de', 'en'], settings.get_subtitle_languages())
        settings.xbmc_language = 'Klingon'
        settings.xbmc_language_code = ''
        self.assertEqual(['en'], settings.get_subtitle_languages())
        settings.subtitle_language = 'en,de'
        self.assertEqual(['en', 'de'], settings.get_subtitle_languages())
