import unittest
from unittest.mock import MagicMock

import requests

from . import fetcher

class TestFetch(unittest.TestCase):

    def test_Fetcher(self):
        sut = fetcher.Fetcher(lambda x: print(x))
        sut.get_HTML('https://www.google.com/') # Doesn't throw

    def test_post_json_reports_http_errors_with_response(self):
        logger = MagicMock()
        sut = fetcher.Fetcher(logger)
        response = MagicMock(ok=False, status_code=503)
        sut.session = MagicMock()
        sut.session.post.return_value = response

        with self.assertRaises(requests.HTTPError) as error:
            sut.post_JSON('https://www.ted.com/graphql', {'query': 'example'})

        self.assertIs(response, error.exception.response)
        self.assertIn('503', str(error.exception))
        self.assertEqual(2, logger.call_count)
