import urllib.parse

from .url_constants import URLTED


__url_search__ = URLTED + '/api/search'
__search_index__ = 'coyote_models_acme_videos_alias_38ce41d1f97ca56a38068f613af166da'
__results_per_page__ = 24


class Search:

    def __init__(self, post_JSON):
        self.post_JSON = post_JSON

    def get_talks_for_search(self, search_string, page_index):
        '''
        Yields number of results left to show after this page,
        then tuples of title, link, img for results on this page.
        '''

        params = urllib.parse.urlencode({
            'query': search_string,
            'hitsPerPage': __results_per_page__,
            'page': page_index - 1,
        })
        response = self.post_JSON(__url_search__, [{
            'indexName': __search_index__,
            'params': params,
        }])
        if response.get('error'):
            raise ValueError('TED search failed: %s' % response['error'])
        results = response.get('results')
        if not results:
            raise ValueError('TED search response did not contain results.')

        search_results = results[0]
        hits = search_results.get('hits')
        if hits is None:
            raise ValueError('TED search response did not contain hits.')

        remaining = max(
            0,
            search_results['nbHits'] -
            (search_results['page'] + 1) * search_results['hitsPerPage'],
        )
        yield remaining

        for result in hits:
            slug = result.get('slug')
            title = result.get('title')
            if not slug or not title:
                continue
            yield title.strip(), URLTED + '/talks/' + slug, self._get_image(result)

    @staticmethod
    def _get_image(result):
        for photo in result.get('photos') or []:
            for photo_size in photo.get('photo_sizes') or []:
                if photo_size.get('url'):
                    return photo_size['url']
        return ''
