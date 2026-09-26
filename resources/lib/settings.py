"""
Contains constants that we initialize to the correct values at runtime.
Should be usable as a testing shim.
"""
import json
import os

from .model import language_mapping

__plugin_id__ = 'plugin.video.ted.talks'
__current_search__ = 'current_search'
__current_search_results__ = 'current_search_results'

# Values of Kodi's locale.subtitlelanguage setting that are not a language.
__kodi_subtitle_special_values__ = ['', 'original', 'default', 'none', 'forced_only']

profile_path = '~/.kodi/userdata/addon_data/plugin.video.ted.talks'
enable_subtitles = True
subtitle_fallback_english = 'false'
xbmc_language = 'English'
xbmc_language_code = ''
kodi_subtitle_language = ''
subtitle_language = 'en'

def __get_kodi_setting__(xbmc, setting_id):
    try:
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue', 'params': {'setting': setting_id}}
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        return response.get('result', {}).get('value') or ''
    except Exception:
        return ''

def init():
    # Kodi provides these modules at runtime; they are not available to the local interpreter.
    # noinspection PyUnresolvedReferences
    import xbmc, xbmcvfs, xbmcaddon
    addon = xbmcaddon.Addon(id=__plugin_id__)
    global profile_path, enable_subtitles, subtitle_fallback_english, xbmc_language, xbmc_language_code, kodi_subtitle_language, subtitle_language
    profile_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    enable_subtitles = addon.getSetting('enable_subtitles')
    subtitle_fallback_english = addon.getSetting('subtitle_fallback_english')
    xbmc_language = xbmc.getLanguage()
    try:
        xbmc_language_code = xbmc.getLanguage(xbmc.ISO_639_1, True)
    except Exception:
        xbmc_language_code = ''
    kodi_subtitle_language = __get_kodi_setting__(xbmc, 'locale.subtitlelanguage')
    subtitle_language = addon.getSetting('subtitle_language')

def get_subtitle_languages():
    '''
    Returns list of TED subtitle language codes in order of preference,
    or None if disabled or no language could be determined.

    Preference: custom codes from the add-on settings, otherwise Kodi's preferred
    subtitle language, otherwise the Kodi interface language.
    '''
    if enable_subtitles == 'false':
        return None

    codes = []
    if subtitle_language.strip():
        for code in subtitle_language.split(','):
            codes += language_mapping.get_ted_language_codes(code)
    else:
        if kodi_subtitle_language.strip().lower() not in __kodi_subtitle_special_values__:
            codes += language_mapping.get_ted_language_codes(kodi_subtitle_language)
        if not codes:
            codes += language_mapping.get_ted_language_codes(xbmc_language_code)
        if not codes:
            try:
                codes += language_mapping.get_ted_language_codes(xbmc_language)
            except Exception:
                pass

    if subtitle_fallback_english == 'true':
        codes.append('en')

    result = []
    for code in codes:
        if code not in result:
            result.append(code)
    return result or None

def __get_profile_path__(*segments):
    return os.path.join(profile_path, *segments)

def set_current_search(value):
    with open(__get_profile_path__('current_search'), 'w') as f:
        f.write(value)

def get_current_search():
    current_search_file = __get_profile_path__('current_search')
    if not os.path.exists(current_search_file):
        return ''
    with open(current_search_file, 'r') as f:
        return f.read()
