"""
Universeller TED-Feed-Parser für Kodi.
Erkennt automatisch RSS- und Atom-Formate (z.B. YouTube, Acast, FeedBurner)
und bereitet die Daten ausfallsicher für Kodi-ListItems auf.
"""

import time
import re
import urllib.request
import urllib.error
import urllib.parse
from xml.etree.ElementTree import fromstring

def get_document(url):
    """
    Lädt das Dokument von der URL herunter und decodiert es sicher als UTF-8-Text.
    """
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kodi/21.0'}
    )
    try:
        usock = urllib.request.urlopen(req, timeout=15)
        raw_data = usock.read()
        usock.close()
        return raw_data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"[TED-Parser] Netzwerkfehler beim Laden von {url}: {e}")
        return ""


class NewTalksRss(object):
    """
    Klasse zum automatischen Erkennen und Parsen von TED-Video-Feeds.
    """

    def __init__(self, logger=None):
        self.logger = logger if logger else print

        # Globale Namespace-Tabelle für alle gängigen Feed-Varianten
        self.namespaces = {
            'atom': 'http://w3.org',
            'itunes': 'http://itunes.com',
            'media': 'http://yahoo.com',
            'feedburner': 'http://rssnamespace.org',
            'yt': 'http://youtube.com'
        }

    def _parse_rss_item(self, item):
        """Verarbeitet ein klassisches RSS <item> Tag (Podcast/FeedBurner)"""
        pub_date_el = item.find('./pubDate')
        pub_date = pub_date_el.text[:-6] if pub_date_el is not None and pub_date_el.text else ""
        try:
            date = time.strptime(pub_date, "%a, %d %b %Y %H:%M:%S")
        except:
            date = time.localtime()

        # Spieldauer berechnen
        duration_el = item.find('./itunes:duration', self.namespaces)
        if duration_el is not None and duration_el.text:
            parts = duration_el.text.split(':')
            if len(parts) == 3: duration = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
            elif len(parts) == 2: duration = int(parts[0])*60 + int(parts[1])
            else: duration = int(parts[0])
        else: duration = 0

        # Titel & Inhalte
        title_el = item.find('./title')
        title = title_el.text.strip() if title_el is not None and title_el.text else "TED Talk"

        plot_el = item.find('./itunes:summary', self.namespaces)
        if plot_el is None: plot_el = item.find('./description')
        plot = plot_el.text.strip() if plot_el is not None and plot_el.text else ""

        thumb_el = item.find('./media:thumbnail', self.namespaces)
        thumb = thumb_el.get('url') if thumb_el is not None else ""

        # Stream-URL (FeedBurner vs. Standard Enclosure)
        media_url = ""
        fb_enclosure = item.find('./feedburner:origEnclosure', self.namespaces)
        if fb_enclosure is not None: media_url = fb_enclosure.get('url')
        if not media_url:
            enclosure = item.find('./enclosure')
            if enclosure is not None: media_url = enclosure.get('url')

        return {
            'title': title, 'cast': ['TED'], 'thumb': thumb, 'plot': plot,
            'duration': duration, 'date': time.strftime("%d.%m.%Y", date),
            'dateadded': time.strftime("%Y-%m-%d %H:%M:%S", date),
            'media': media_url, 'mediatype': 'video'
        }

    def _parse_atom_entry(self, entry):
        """Verarbeitet ein Atom <entry> Tag (z.B. YouTube-Kanäle)"""
        title_el = entry.find('./atom:title', self.namespaces)
        title = title_el.text.strip() if title_el is not None and title_el.text else "YouTube Video"

        # YouTube Video ID auslesen
        yt_id_el = entry.find('./yt:videoId', self.namespaces)
        if yt_id_el is not None and yt_id_el.text:
            # Übersetzung in den internen Kodi-YouTube-Addon-Pfad
            media_url = f"plugin://plugin.video.youtube/play/?video_id={yt_id_el.text}"
        else:
            link_el = entry.find('./atom:link[@rel="alternate"]', self.namespaces)
            media_url = link_el.get('href') if link_el is not None else ""

        # Thumbnail & Plot via Media-Namespace extrahieren
        thumb_el = entry.find('.//media:thumbnail', self.namespaces)
        thumb = thumb_el.get('url') if thumb_el is not None else ""

        plot_el = entry.find('.//media:description', self.namespaces)
        plot = plot_el.text.strip() if plot_el is not None and plot_el.text else ""

        pub_el = entry.find('./atom:published', self.namespaces)
        pub_date = pub_el.text[:19] if pub_el is not None and pub_el.text else ""
        try:
            date = time.strptime(pub_date, "%Y-%m-%dT%H:%M:%S")
        except:
            date = time.localtime()

        return {
            'title': title, 'cast': ['TED YouTube'], 'thumb': thumb, 'plot': plot,
            'duration': 0, 'date': time.strftime("%d.%m.%Y", date),
            'dateadded': time.strftime("%Y-%m-%d %H:%M:%S", date),
            'media': media_url, 'mediatype': 'video'
        }

    def get_new_talks(self, feed=None):
        if not feed:
            # Ausfallsicherer, moderner Haupt-Video-Feed von YouTube (TED-Kanal)
            feed = 'https://youtube.com'

        talks_by_title = {}
        rss_text = get_document(feed)
        if not rss_text:
            return iter([])

        # XML-Token-Fehler bereinigen
        rss_clean = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+);)', '&amp;', rss_text)

        try:
            root = fromstring(rss_clean)

            # FORMAT-ERKENNUNG: Prüfen, ob es ein Atom- oder RSS-Feed ist
            if 'feed' in root.tag: # Atom-Standard (z.B. YouTube)
                entries = root.findall('.//atom:entry', self.namespaces)
                self.logger(f"[TED-Parser] Atom-Format erkannt. {len(entries)} Einträge gefunden.")
                for entry in entries:
                    talk = self._parse_atom_entry(entry)
                    if talk['title'] and talk['media']:
                        talks_by_title[str(talk['title'])] = talk

            else: # Klassisches RSS-Format (z.B. Podcast-Feeds)
                items = root.findall('.//item')
                self.logger(f"[TED-Parser] RSS-Format erkannt. {len(items)} Einträge gefunden.")
                for item in items:
                    talk = self._parse_rss_item(item)
                    if talk['title'] and talk['media']:
                        talks_by_title[str(talk['title'])] = talk

        except Exception as e:
            self.logger(f"[TED-Parser] Kritischer XML-Parser-Fehler: {e}")

        return iter(talks_by_title.values())


# --- Lokaler Testlauf außerhalb von Kodi ---
if __name__ == '__main__':
    parser = NewTalksRss()

    # 1. Test mit dem modernen YouTube Atom-Video-Feed
    print("\n--- Teste YouTube-Atom-Feed ---")
    yt_videos = parser.get_new_talks('https://youtube.com')
    for i, v in enumerate(yt_videos):
        if i >= 2: break
        print(f"Gefunden: {v['title']}\n  Pfad -> {v['media']}")

    # 2. Test mit einem alternativen Podcast-RSS-Feed (Falls gewünscht)
    print("\n--- Teste Podcast-RSS-Feed ---")
    podcast_videos = parser.get_new_talks('https://feeds.acast.com/public/shows/67587e77c705e441797aff96')
    for i, v in enumerate(podcast_videos):
        if i >= 2: break
        print(f"Gefunden: {v['title']}\n  Stream -> {v['media']}")
