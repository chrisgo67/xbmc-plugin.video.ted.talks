"""
Contains constants that we initialize to the correct values at runtime.
"""
import sys

__plugin__ = "TED Talks Uninitialized Plugin"
getLS = lambda x: x
__pluginLS__ = __plugin__
__author__ = "XXX"
__version__ = "X.X.X"


def init():
    # Kodi provides this module at runtime; it is not available to the local interpreter.
    # noinspection PyUnresolvedReferences
    import xbmcaddon
    addon = xbmcaddon.Addon(id='plugin.video.ted.talks')
    global __plugin__, getLS, __author__, __version__, __pluginLS__
    __plugin__ = addon.getAddonInfo('name')
    getLS = addon.getLocalizedString
    __pluginLS__ = getLS(30000)
    __author__ = addon.getAddonInfo('author')
    __version__ = addon.getAddonInfo('version')
    # Kodi provides this module at runtime; it is not available to the local interpreter.
    # noinspection PyUnresolvedReferences
    import xbmc
    xbmc.log("[ADDON] Initialized %s v%s using Python: %s'" % (__plugin__, __version__, sys.version), level=xbmc.LOGINFO)

def localize(string_id, fallback):
    '''
    Localized string, or the English fallback when running outside Kodi.
    '''
    text = getLS(string_id)
    return text if isinstance(text, str) and text else fallback

def report(gnarly_message, friendly_message=None, level='info'):
    '''
    Log a message with optional onscreen notification.
    '''
    # Kodi provides this module at runtime; it is not available to the local interpreter.
    # noinspection PyUnresolvedReferences
    import xbmc
    level = {'info' : xbmc.LOGINFO, 'debug': xbmc.LOGDEBUG}[level]
    xbmc.log("[ADDON] %s v%s - %s" % (__plugin__, __version__, gnarly_message), level=level)
    if friendly_message:
        xbmc.executebuiltin('Notification("%s","%s",)' % (__pluginLS__, friendly_message))
