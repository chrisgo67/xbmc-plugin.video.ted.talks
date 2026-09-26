"""
Grab new talks from RSS feed. Yes we can just add an rss: source in XBMC,
but this allows us a little more power to tweak things how we want them,
so keep it for now.
"""

import re
from datetime import timedelta
import time
import urllib.request, urllib.error, urllib.parse


try:
    from elementtree.ElementTree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring

ITUNES_NS = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
MEDIA_NS = '{http://search.yahoo.com/mrss/}'

# feeds.feedburner.com/tedtalks_video stopped receiving new talks. TED's
# "TED Talks Daily" show on Acast is the feed that is actually kept current;
# its <link> for each item still redirects to the talk's ted.com page, which
# is what get_talk_details/playVideo actually need.
FEED_URL = 'https://feeds.acast.com/public/shows/67587e77c705e441797aff96'

# Acast items append an HTML "Hosted on Acast..." disclaimer after an <hr>.
_ACAST_BOILERPLATE_RE = re.compile(r'<hr>.*', re.DOTALL)
_TAG_RE = re.compile(r'<[^>]+>')


def get_document(url):
    """
    Return document at given URL.
    """
    usock = urllib.request.urlopen(url)
    try:
        return usock.read()
    finally:
        usock.close()


def _clean_summary(text):
    """Strip markup and the Acast hosting disclaimer from a summary/description."""
    text = _ACAST_BOILERPLATE_RE.sub('', text)
    return _TAG_RE.sub('', text).strip()


def _parse_duration_seconds(duration):
    """
    Parse an itunes:duration value, which may be plain seconds, 'M:S' or 'H:M:S'.
    """
    parts = [int(part) for part in duration.split(':')]
    while len(parts) < 3:
        parts.insert(0, 0)
    hours, minutes, seconds = parts[-3:]
    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


class NewTalksRss(object):
    """
    Fetches new talks from RSS stream.
    """

    def __init__(self, logger):
        self.logger = logger
        self.default_thumb = ''  # populated per-feed from the channel's cover image

    def get_talk_details(self, item):
        """
        Return the details from an RSS <item> tag soup.
        """
        # <title> is "Talk title | Speaker name"; there's no separate itunes:author/subtitle.
        title_el = item.find('./title')
        title = title_el.text.strip() if title_el is not None and title_el.text else 'TED Talk'
        author = 'TED'
        if ' | ' in title:
            title, _, author = title.rpartition(' | ')

        pic = self.default_thumb
        thumb_el = item.find('./%sthumbnail' % MEDIA_NS)
        if thumb_el is None:
            thumb_el = item.find('./%simage' % ITUNES_NS)
        if thumb_el is not None:
            pic = thumb_el.get('url') or thumb_el.get('href') or pic

        self.logger('%s = %s' % ('pic', str(pic)), level='debug')

        duration_el = item.find('./%sduration' % ITUNES_NS)
        duration_seconds = _parse_duration_seconds(duration_el.text.strip()) if duration_el is not None and duration_el.text else 0.0

        plot_el = item.find('./%ssummary' % ITUNES_NS)
        if plot_el is None or not plot_el.text:
            plot_el = item.find('./description')
        plot = _clean_summary(plot_el.text) if plot_el is not None and plot_el.text else ''

        link = item.find('./link').text

        # Get date as XBMC wants it. Timezone suffix ("+0000" or "GMT") varies
        # in length, but the "%a, %d %b %Y %H:%M:%S" part is always 25 chars.
        pub_date = item.find('./pubDate').text[:25]
        try:
            date = time.strptime(pub_date, "%a, %d %b %Y %H:%M:%S")
        except ValueError as e:
            self.logger("Could not parse date '%s': %s" % (pub_date, e))
            date = time.localtime()
        date = time.strftime("%d.%m.%Y", date)

        return {'title':title, 'author':author, 'thumb':pic, 'plot':plot, 'duration':duration_seconds, 'date':date, 'link':link, 'mediatype': "video"}

    def __total_seconds__(self, delta):
        return delta.total_seconds()

    def get_new_talks(self):
        """
        Returns talks as dicts {title:, author:, thumb:, date:, duration:, link:}.
        """
        talks_by_title = {}
        rss = get_document(FEED_URL)
        root = fromstring(rss)

        channel = root.find('./channel')
        image_el = channel.find('./%simage' % ITUNES_NS) if channel is not None else None
        self.default_thumb = image_el.get('href') if image_el is not None else ''

        for item in root.findall('channel/item'):
            talk = self.get_talk_details(item)
            talks_by_title[talk['title']] = talk

        return iter(talks_by_title.values())

