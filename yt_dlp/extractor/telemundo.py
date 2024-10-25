from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import determine_ext, find_json


class TelemundoIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?telemundo\.com\/.+(?P<id>\d{5,})'
    _TESTS = []

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        metadata = self._search_nextjs_data(webpage, video_id)

        format_url = find_json(metadata, 'videoAssets', fatal=True)[0]['publicUrl']

        ext = determine_ext(format_url, '')
        if ext == '':
            redirect_url = self._request_webpage(HEADRequest(format_url), video_id, 'Processing format url', fatal=False).url
            format_url = redirect_url if redirect_url else format_url

        ext = determine_ext(format_url)
        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(
                format_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats = [{
                'url': format_url,
                'ext': ext if ext else 'mp4',
                'format_id': 'http',
            }]

        return {
            'url': url,
            'id': video_id,
            'title': self._html_search_meta(['name', 'og:title'], webpage, fatal=False),
            'formats': formats,
        }
