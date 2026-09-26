from .. import plugin
from .next_data import get_image, get_page_props
from .url_constants import URLTED

__url_topics__ = URLTED + '/topics'
__url_graphql__ = URLTED + '/graphql'

__topic_videos_query__ = """
query($slug: String!, $after: String) {
  topic(slug: $slug) {
    videos(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { title slug presenterDisplayName primaryImageSet { url aspectRatioName } }
    }
  }
}
"""

class Topics:

    def __init__(self, get_HTML, logger, post_JSON=None):
        self.get_HTML = get_HTML
        self.logger = logger
        self.post_JSON = post_JSON

    def get_topics(self):
        '''
        Yields tuples of title, topic slug.
        '''
        groups = get_page_props(self.get_HTML(__url_topics__)).get('list') or []
        for group in groups:
            for item in group.get('items') or []:
                title = (item.get('name') or '').strip()
                if title and item.get('slug'):
                    yield title, item['slug']

    def get_talks(self, topic):
        '''
        Yields tuples of title, link, img, speaker.
        '''
        after = None
        while True:
            response = self.post_JSON(__url_graphql__, {
                'query': __topic_videos_query__,
                'variables': {'slug': topic, 'after': after},
            })
            topic_data = (response.get('data') or {}).get('topic')
            if topic_data is None:
                msg = "Cannot find talks for topic '%s'." % (topic)
                friendly_message = plugin.localize(30123, "Cannot find talks for topic '%s'.") % (topic)
                self.logger('%s\n%s' % (msg, response.get('errors')), friendly_message=friendly_message)
                return

            videos = topic_data['videos']
            for talk in videos.get('nodes') or []:
                yield (talk['title'].strip(), URLTED + '/talks/' + talk['slug'],
                       get_image(talk.get('primaryImageSet')), talk.get('presenterDisplayName'))

            page_info = videos.get('pageInfo') or {}
            if not page_info.get('hasNextPage'):
                return
            after = page_info.get('endCursor')
