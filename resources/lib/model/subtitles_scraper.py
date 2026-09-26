'''
Fetches TED subtitles as WebVTT (listed in the HLS metadata of a talk) and converts them to SRT.
'''

import re

from .. import plugin

__timestamp_re__ = re.compile(r'(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})')


class Subtitles:

    def __init__(self, fetcher, logger):
        self.fetcher = fetcher
        self.logger = logger

    def __format_time__(self, time):
        millis = time % 1000
        seconds = (time // 1000) % 60
        minutes = (time // 60000) % 60
        hours = time // 3600000
        return '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, millis)

    def __parse_time__(self, text):
        match = __timestamp_re__.match(text.strip())
        if not match:
            raise ValueError("Bad WebVTT timestamp '%s'" % (text))
        hours, minutes, seconds, millis = match.groups()
        return ((int(hours or 0) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)

    def __vtt_to_srt__(self, vtt):
        '''
        Converts WebVTT to SRT. Cue identifiers, settings, NOTE/STYLE/REGION blocks are dropped.
        '''
        result = []
        blocks = re.split(r'\n\s*\n', vtt.replace('\r\n', '\n').replace('\r', '\n').strip())
        for block in blocks:
            lines = block.split('\n')
            timing_index = next((i for i, l in enumerate(lines) if '-->' in l), None)
            if timing_index is None:
                continue  # Header, NOTE, STYLE or REGION block.
            start, end = lines[timing_index].split('-->', 1)
            end = end.strip().split()[0] if end.strip() else end
            text = '\n'.join(lines[timing_index + 1:]).strip()
            if not text:
                continue
            result.append('%d\n%s --> %s\n%s\n' % (
                len(result) + 1,
                self.__format_time__(self.__parse_time__(start)),
                self.__format_time__(self.__parse_time__(end)),
                text))
        return '\n'.join(result) + '\n' if result else ''

    def __get_available_subtitles__(self, player_json):
        '''
        Returns a list of (language code, WebVTT url) in the order TED lists them.
        '''
        # Strip the intro parameters as talk_scraper does for the stream, otherwise the subtitles lag.
        metadata_url = player_json['resources']['hls']['metadata'].split('?', 1)[0]
        metadata = self.fetcher.get(metadata_url).json()
        return [(s['code'], s['webvtt']) for s in metadata.get('subtitles') or [] if s.get('code') and s.get('webvtt')]

    def get_subtitles_for_talk(self, player_json, accepted_languages):
        '''
        Return subtitles in srt format, or notify the user and return None if there was a problem.
        '''
        try:
            available = dict(self.__get_available_subtitles__(player_json))

            if not available:
                self.logger('No subtitles found', friendly_message=plugin.localize(30120, 'No subtitles found'))
                return None

            language_matches = [l for l in accepted_languages if l in available]
            if not language_matches:
                accepted = ','.join(accepted_languages)
                self.logger('No subtitles in: {}'.format(accepted),
                            friendly_message=plugin.localize(30121, 'No subtitles in: %s') % (accepted))
                return None

            vtt = self.fetcher.get(available[language_matches[0]])
            vtt.encoding = 'utf-8'
            return self.__vtt_to_srt__(vtt.text) or None

        except Exception as e:
            # Graceful degradation: let video play without subtitles.
            self.logger('Could not display subtitles: {}'.format(e), friendly_message=plugin.localize(30122, 'Error showing subtitles'))
            return None
