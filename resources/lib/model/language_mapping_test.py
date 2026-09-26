import unittest
from . import language_mapping

class TestLanguageMapping(unittest.TestCase):

    def test_get_language_code(self):
        self.assertEqual("de", language_mapping.get_language_code("German"))
        self.assertEqual("de", language_mapping.get_language_code("german"))
        self.assertEqual("de", language_mapping.get_language_code("German (sausage)"))
        self.assertEqual(None, language_mapping.get_language_code("Herman (sausage)"))
        self.assertEqual("nl", language_mapping.get_language_code("Dutch"))
        self.assertEqual("nl", language_mapping.get_language_code("Flemish"))

    def test_get_ted_language_codes_plain(self):
        self.assertEqual(['de'], language_mapping.get_ted_language_codes('de'))
        self.assertEqual(['de'], language_mapping.get_ted_language_codes('German'))
        self.assertEqual([], language_mapping.get_ted_language_codes('Klingon'))
        self.assertEqual([], language_mapping.get_ted_language_codes(''))
        self.assertEqual([], language_mapping.get_ted_language_codes(None))

    def test_get_ted_language_codes_region(self):
        self.assertEqual(['de-de', 'de'], language_mapping.get_ted_language_codes('de-DE'))
        self.assertEqual(['de-at', 'de'], language_mapping.get_ted_language_codes('de_AT'))
        self.assertEqual(['pt-br', 'pt'], language_mapping.get_ted_language_codes('pt-BR'))
        self.assertEqual(['pt', 'pt-br'], language_mapping.get_ted_language_codes('pt-PT'))
        self.assertEqual(['fr-ca', 'fr'], language_mapping.get_ted_language_codes('fr-CA'))

    def test_get_ted_language_codes_ted_specific(self):
        self.assertEqual(['zh-cn', 'zh-tw'], language_mapping.get_ted_language_codes('zh'))
        self.assertEqual(['zh-tw', 'zh-cn'], language_mapping.get_ted_language_codes('zh-HK'))
        self.assertEqual(['zh-us', 'zh-cn', 'zh-tw'], language_mapping.get_ted_language_codes('zh-US'))
        self.assertEqual(['nb'], language_mapping.get_ted_language_codes('no'))
        self.assertEqual(['he'], language_mapping.get_ted_language_codes('iw'))

    def test_get_ted_language_codes_kodi_names(self):
        self.assertEqual(['pt-br', 'pt'], language_mapping.get_ted_language_codes('Portuguese (Brazil)'))
        self.assertEqual(['zh-cn', 'zh-tw'], language_mapping.get_ted_language_codes('Chinese (Simple)'))
        self.assertEqual(['zh-tw', 'zh-cn'], language_mapping.get_ted_language_codes('Chinese (Traditional)'))
        self.assertEqual(['fr-ca', 'fr'], language_mapping.get_ted_language_codes('French (Canada)'))
        self.assertEqual(['nb'], language_mapping.get_ted_language_codes('Norwegian'))