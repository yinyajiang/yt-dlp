from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class Anime1IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?anime1.cc/.+'

    _TESTS = []

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None)
        title = self._html_search_meta(['description'], webpage)
        m3u8_url = self._html_search_regex("(https://.+index\\.m3u8)", webpage, 'url')
        if not m3u8_url:
            raise ExtractorError('Unable to find m3u8 URL')
        id = self._search_regex("/([^/]+?)/index\\.m3u8", m3u8_url, 'id', fatal=False, group=1)
        formats = self._extract_m3u8_formats(m3u8_url, id)
        return {
            'id': id,
            'title': title,
            'formats': formats,
        }
