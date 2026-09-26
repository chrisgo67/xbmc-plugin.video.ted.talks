from .next_data import get_image, get_page_props
from .url_constants import URLTED

__url_speakers__ = URLTED + '/speakers?page=%s'

class Speakers:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def __get_speaker_page__(self, index):
        return get_page_props(self.get_HTML(__url_speakers__ % (index)))['directory']

    def __get_speaker_page_count__(self, directory):
        return int(directory['pageInfo']['pageCount'])

    def get_speaker_page_count(self):
        return self.__get_speaker_page_count__(self.__get_speaker_page__(1))

    def get_speakers_for_pages(self, pages):
        '''
        First yields the number of pages of speakers.
        After that yields tuples of title, link, img.
        '''

        returned_count = False
        for page in pages:
            directory = self.__get_speaker_page__(page)
            if not returned_count:
                returned_count = True
                yield self.__get_speaker_page_count__(directory)

            for speaker in directory.get('speakers') or []:
                title = ' '.join((speaker.get('fullName') or '').split()) # Normalize whitespace.
                url = URLTED + '/speakers/' + speaker['slug']
                yield title, url, speaker.get('avatar')

    def get_talks_for_speaker(self, url):
        '''
        Yields tuples of title, link, img.
        '''
        speaker = get_page_props(self.get_HTML(url)).get('state', {}).get('speaker') or {}
        for talk in speaker.get('talks') or []:
            yield talk['title'].strip(), URLTED + '/talks/' + talk['slug'], get_image(talk.get('primaryImageSet'))
