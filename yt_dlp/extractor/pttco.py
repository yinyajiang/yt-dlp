import re
import urllib.parse

from .common import ExtractorError, InfoExtractor
from ..utils import get_elements_html_by_class


class PttcoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ptt.co/(?:[\w\-]+/)?(?P<plid>[0-9]+)/(?P<id>[0-9]+)/?'
    _TRY_GENERIC = True

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_extract_title(webpage).strip()
        playlist_id = self._match_valid_url(url).group('plid')
        if '_single_' in url:
            if '_trimtitle_' in url:
                title = title.split(':')[0].strip()
            return self._extract_video(webpage, video_id, title)

        seqs = [seq for seq in self._fetch_seqs_urls(webpage, url, fatal=False) if playlist_id in seq]
        if len(seqs) > 1 and any(f'/{playlist_id}/{video_id}' in seq for seq in seqs):
            if not self._downloader.params.get('extract_flat', False):
                entries = [info for info in [self.__real_extract(seq, fatal=False) for seq in seqs] if info]
                if entries:
                    return self.playlist_result(entries, playlist_id=playlist_id, playlist_title=self._playlist_title(title, playlist_id))
            else:
                return self._result_url_playlist(self, seqs, playlist_id=playlist_id, playlist_title=self._playlist_title(title, playlist_id))

        return self._extract_video(webpage, video_id, title)

    def _extract_video(self, webpage, video_id, title, fatal=False):
        try:
            js = self._search_json_ld(webpage, video_id)
            fmts = []
            if not getattr(self, '_direct_m3u8_info', False):
                fmts = self._extract_m3u8_formats(js['url'], video_id, 'ts')
                if len(fmts) == 1 and fmts[0]['url'] == js['url'] and fmts[0]['ext'] == 'ts':
                    self._direct_m3u8_info = fmts[0]
            else:
                info = self._direct_m3u8_info
                info['url'] = js['url']
                fmts = [info]

            return {
                'id': video_id,
                'title': title if title else js.get('title', video_id),
                'thumbnails': js.get('thumbnails'),
                'duration': js.get('duration'),
                'view_count': js.get('view_count'),
                'formats': fmts,
            }
        except Exception:
            if fatal:
                raise
            return None

    def __real_extract(self, url, fatal=False):
        try:
            video_id = self._match_id(url)
            webpage = self._download_webpage(url, video_id)
            title = self._html_extract_title(webpage).strip()
            return self._extract_video(webpage, video_id, title, fatal=fatal)
        except Exception:
            if fatal:
                raise
            return None

    @staticmethod
    def _playlist_title(title, playlist_id):
        title = title.split('-')[0].strip()
        if not title:
            title = playlist_id
        return title

    @staticmethod
    def _fetch_seqs_urls(webpage, origin_url, fatal=False):
        seqs = get_elements_html_by_class('seq', webpage)
        herfs = []
        for seq in seqs:
            match = re.search(r'href\s*=\s*([\'"])([^"\']+)(?:\1)', seq)
            if not match:
                continue
            herfs.append(match.group(2))
        if not herfs:
            if fatal:
                raise ExtractorError('Unable to find seq')
            return []
        herfs = list(set(herfs))

        def _fetch_num(x):
            try:
                return int(re.search(r'([0-9]+)/(?P<id>[0-9]+)/?', x).group('id'))
            except AttributeError:
                return 0

        herfs = sorted(herfs, key=_fetch_num)

        base_url = re.match(r'(https?://[^/]+)', origin_url).group(1)

        def _url_process(u):
            if not u.startswith('http'):
                u = urllib.parse.urljoin(base_url, u)
            if '?' in u:
                return f'{u}&_single_=1'
            else:
                return f'{u}?_single_=1'

        return [_url_process(href) for href in herfs]

    @staticmethod
    def _result_url_playlist(ie, seqs, playlist_id, playlist_title):
        return ie.playlist_result([
            {
                'url': href,
                'title': f'{playlist_title if playlist_title else playlist_id} - {idx + 1}',
                '_type': 'url',
            } for idx, href in enumerate(seqs)
        ], playlist_id=playlist_id, playlist_title=playlist_title)


class PttcoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ptt.co/(?:[\w\-]+/)?v/(?P<id>[0-9]+)/?'
    _TRY_GENERIC = True

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        title = PttcoIE._playlist_title(self._html_extract_title(webpage), playlist_id)
        herfs = PttcoIE._fetch_seqs_urls(webpage, url, fatal=True)
        if self._is_as_single_video(herfs, playlist_id):
            single_url = herfs[0]
            if '?' in single_url:
                single_url = f'{single_url}&_trimtitle_=1'
            else:
                single_url = f'{single_url}?_trimtitle_=1'
            return self.url_result(single_url, PttcoIE)
        return PttcoIE._result_url_playlist(self, herfs, playlist_id=playlist_id, playlist_title=title)

    def _is_as_single_video(self, herfs, vid):
        if len(herfs) == 1:
            return True
        return bool(len(herfs) <= 4 and any(v in herfs[1] for v in [f'{vid}/720', f'{vid}/1080', f'{vid}/2160', f'{vid}/4k']))
