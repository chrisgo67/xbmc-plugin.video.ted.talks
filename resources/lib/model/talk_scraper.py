# 2022-03 Convert to use regular expressions
import json
import requests
import re
import sys
# Kodi provides this module at runtime; it is not available to the local interpreter.
# noinspection PyUnresolvedReferences
import xbmc

# get() used in Kodi 18.x
def get(html, logger, video_quality='180kbps'):
    '''Extract talk details from talk html
       @param video_quality string in form '\\d+kbps' that should match one of the provided TED bitrates.
    '''

    match = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', re.DOTALL).search(html)
    if not match:
        raise Exception('Could not parse HTML.')
    init_scripts = match.group(1)
    xbmc.log(msg='%s = %s' % ('init_scripts', str(init_scripts)), level=xbmc.LOGDEBUG)

    init_json = json.loads(init_scripts, strict=False)
    talk_json = init_json['props']['pageProps']['videoData']

    # Current TED pages provide player data as a JSON object in 'videoPlayerData';
    # older pages provided it as an escaped JSON string in 'playerData'.
    player_json = talk_json.get('videoPlayerData')
    if not player_json:
        player_raw = talk_json.get('playerData')
        if not player_raw:
            raise Exception('Could not parse HTML for playerData.')
        player_json = json.loads(player_raw) if isinstance(player_raw, str) else player_raw
    xbmc.log(msg='%s = %s' % ('player_json', str(player_json)), level=xbmc.LOGDEBUG)

    title = str(talk_json.get('title') or player_json.get('title') or '')
    xbmc.log(msg='%s = %s' % ('title', title), level=xbmc.LOGDEBUG)

    speaker = str(player_json.get('speaker') or talk_json.get('presenterDisplayName') or '')
    xbmc.log(msg='%s = %s' % ('speaker', speaker), level=xbmc.LOGDEBUG)

    #xbmc.log(msg='%s = %s' % ('sys.version_info.major', sys.version_info.major), level=xbmc.LOGDEBUG)
    #if sys.version_info.major < 3:
    #    url = player_json['resources']['h264'][0]['file']
    #else:
    #    url = player_json['resources']['hls']['stream']
    url = player_json['resources']['hls']['stream']
    xbmc.log(msg='%s = %s' % ('url', url), level=xbmc.LOGDEBUG)

    # Remove default intro as it messes up the subtitle timing
    pos_of_question_mark = str(url).find('?')
    if pos_of_question_mark >= 0:
        url = str(url)[0:pos_of_question_mark]
    xbmc.log(msg='%s = %s' % ('url intro removed', url), level=xbmc.LOGDEBUG)

    plot = str(talk_json.get('description') or '')
    xbmc.log(msg='%s = %s' % ('plot', plot), level=xbmc.LOGDEBUG)

    return url, title, speaker, plot, talk_json, player_json

# get_talk() used in Kodi 19+
def get_talk(html, logger):
    url, title, speaker, plot, talk_json, player_json = get(html, logger)
    return url, title, speaker, plot, talk_json, player_json
