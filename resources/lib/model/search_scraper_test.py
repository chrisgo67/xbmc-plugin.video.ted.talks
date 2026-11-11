import unittest

from .search_scraper import Search, __search_index__, __url_search__
from .url_constants import URLTED


class TestSearchScraper(unittest.TestCase):

    def setUp(self):
        self.payloads = []
        self.response = {
            'results': [{
                'nbHits': 50,
                'page': 0,
                'hitsPerPage': 24,
                'hits': [
                    {
                        'title': 'Grüße aus München',
                        'slug': 'gruesse_aus_muenchen',
                        'photos': [{
                            'photo_sizes': [{'url': 'https://example.com/talk.jpg'}],
                        }],
                    },
                    {
                        'title': 'Ein weiterer Talk',
                        'slug': 'ein_weiterer_talk',
                        'photos': [],
                    },
                ],
            }],
        }

        def post_json(url, payload):
            self.payloads.append((url, payload))
            return self.response

        self.sut = Search(post_json)

    def test_search_encodes_unicode_and_extracts_talks(self):
        talks = self.sut.get_talks_for_search('Müller & Grüße', 1)

        self.assertEqual(26, next(talks))
        self.assertEqual([
            ('Grüße aus München', URLTED + '/talks/gruesse_aus_muenchen',
             'https://example.com/talk.jpg'),
            ('Ein weiterer Talk', URLTED + '/talks/ein_weiterer_talk', ''),
        ], list(talks))

        url, payload = self.payloads[0]
        self.assertEqual(__url_search__, url)
        self.assertEqual(__search_index__, payload[0]['indexName'])
        self.assertEqual(
            'query=M%C3%BCller+%26+Gr%C3%BC%C3%9Fe&hitsPerPage=24&page=0',
            payload[0]['params'],
        )

    def test_search_requests_next_zero_based_api_page(self):
        self.response['results'][0]['page'] = 1
        self.response['results'][0]['nbHits'] = 50

        talks = self.sut.get_talks_for_search('nuclear', 2)

        self.assertEqual(2, next(talks))
        self.assertIn('page=1', self.payloads[0][1][0]['params'])

    def test_search_reports_api_errors(self):
        self.response = {'error': 'Search service unavailable', 'results': []}

        with self.assertRaisesRegex(ValueError, 'Search service unavailable'):
            next(self.sut.get_talks_for_search('nuclear', 1))
