"""
Contains constants that we initialize to the correct values at runtime.
"""
import sys

# Kodi provides these modules at runtime; they are not available to the local interpreter.
try:
    import xbmc  # pylint: disable=import-error
except ImportError:
    xbmc = None
try:
    import xbmcaddon  # pylint: disable=import-error
except ImportError:
    xbmcaddon = None

_STATE = {
    'name': "TED Talks Uninitialized Plugin",
    'name_ls': "TED Talks Uninitialized Plugin",
    'author': "XXX",
    'version': "X.X.X",
    'addon': None,
}


def get_localized_string(string_id):
    '''
    Localized string from Kodi, or the id itself when running outside Kodi.
    '''
    addon = _STATE['addon']
    return addon.getLocalizedString(string_id) if addon else string_id


def init():
    '''
    Read add-on metadata from Kodi; must be called once at startup.
    '''
    addon = xbmcaddon.Addon(id='plugin.video.ted.talks')
    _STATE['addon'] = addon
    _STATE['name'] = addon.getAddonInfo('name')
    _STATE['name_ls'] = get_localized_string(30000)
    _STATE['author'] = addon.getAddonInfo('author')
    _STATE['version'] = addon.getAddonInfo('version')
    xbmc.log(f"[ADDON] Initialized {_STATE['name']} v{_STATE['version']} using Python: {sys.version}'",
             level=xbmc.LOGINFO)


def localize(string_id, fallback):
    '''
    Localized string, or the English fallback when running outside Kodi.
    '''
    text = get_localized_string(string_id)
    return text if isinstance(text, str) and text else fallback


def report(gnarly_message, friendly_message=None, level='info'):
    '''
    Log a message with optional onscreen notification.
    '''
    level = {'info': xbmc.LOGINFO, 'debug': xbmc.LOGDEBUG}[level]
    xbmc.log(f"[ADDON] {_STATE['name']} v{_STATE['version']} - {gnarly_message}", level=level)
    if friendly_message:
        xbmc.executebuiltin(f'Notification("{_STATE["name_ls"]}","{friendly_message}",)')
