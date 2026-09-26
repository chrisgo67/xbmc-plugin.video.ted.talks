import json
import re

__next_data_re__ = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)


def get_page_props(html):
    '''
    Extracts the Next.js page props embedded in TED pages.
    '''
    match = __next_data_re__.search(html)
    if not match:
        raise ValueError('No __NEXT_DATA__ found in page.')
    return json.loads(match.group(1))['props']['pageProps']


def get_image(image_set, preferred=('16x9', '4x3', '2x1')):
    '''
    Picks an image URL from a TED primaryImageSet list.
    '''
    if not image_set:
        return None
    by_ratio = dict((i.get('aspectRatioName'), i.get('url')) for i in image_set)
    for ratio in preferred:
        if by_ratio.get(ratio):
            return by_ratio[ratio]
    return image_set[0].get('url')
