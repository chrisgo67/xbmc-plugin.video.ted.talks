import timeit
import unittest

from .speakers_scraper import Speakers
from .test_util import skip_ted_rate_limited, CachedHTMLProvider

class TestSpeakersScraper(unittest.TestCase):

    def setUp(self):
        self.sut = Speakers(CachedHTMLProvider().get_HTML)

    def test_get_speaker_page_count(self):
        count = self.sut.get_speaker_page_count()
        self.assertLessEqual(64, count)

    def test_get_speakers_for_pages(self):
        speakers_generator = self.sut.get_speakers_for_pages([1])
        self.assertTrue(next(timeit.itertools.islice(speakers_generator, 1)) > 1)

        e_speakers = list(speakers_generator)

        self.assertTrue(len(e_speakers) > 0)
        self.assertEqual(30, len(e_speakers))  # 30 per page

        sample_speaker = [s for s in e_speakers if s[0] == 'Jennifer Aaker'][0]
        self.assertEqual('https://www.ted.com/speakers/jennifer_aaker', sample_speaker[1])
        self.assertTrue(sample_speaker[2].startswith('https://'))

    @skip_ted_rate_limited
    def test_get_speakers_performance(self):
        scraper = self.sut
        # Run once to cache.
        speakers = list(scraper.get_speakers_for_pages([3, 4]))
        print(("%s speakers found" % (len(speakers) - 1)))  # -1 because we yield #pages first

        def test():
            self.assertEqual(len(speakers), len(list(scraper.get_speakers_for_pages([3, 4]))))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print(("Getting speakers list took %s seconds per run" % (time)))
        self.assertGreater(1, time)

    def test_get_talks_for_speaker(self):
        talks = list(self.sut.get_talks_for_speaker("https://www.ted.com/speakers/janine_benyus"))
        self.assertLessEqual(2, len(talks))  # 2 at time of writing

        talk = [t for t in talks if t[0] == "Biomimicry's surprising lessons from nature's engineers"][0]
        self.assertEqual('https://www.ted.com/talks/janine_benyus_biomimicry_s_surprising_lessons_from_nature_s_engineers', talk[1])
        self.assertTrue(talk[2].startswith('https://'))
