import os

import xbmc
import xbmcaddon
import xbmcvfs


class TedSubtitlePlayer(xbmc.Player):

    def onAVStarted(self):
        playlist_file = os.path.join(xbmcvfs.translatePath('special://temp/'), 'ted_talks.m3u8')
        if os.path.normcase(os.path.normpath(self.getPlayingFile())) != os.path.normcase(os.path.normpath(playlist_file)):
            return
        if xbmcaddon.Addon(id='plugin.video.ted.talks').getSetting('enable_subtitles') != 'true':
            return

        subtitles_file = os.path.join(xbmcvfs.translatePath('special://temp/'), 'ted_talks_subs.srt')
        if os.path.isfile(subtitles_file) and os.path.getsize(subtitles_file):
            self.setSubtitles(subtitles_file)
            self.showSubtitles(True)


if __name__ == '__main__':
    player = TedSubtitlePlayer()
    xbmc.Monitor().waitForAbort()
