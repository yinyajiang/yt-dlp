from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import determine_ext, try_get


class TelemundoIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?telemundo\.com\/.+(?P<id>\d{5,})'
    _TESTS = []

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        metadata = self._search_nextjs_data(webpage, video_id)

        format_url = try_get(
            metadata,
            lambda x: x['props']['initialState']['article']['content'][0]['primaryMedia']['video']['videoAssets'][0]['publicUrl'])
        if not format_url:
            self.raise_no_formats('not found video format: x[props][initialState][article][content][0][primaryMedia][video][videoAssets][0][publicUrl]', expected=True, video_id=video_id)

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
            'title': self._search_regex(r'<h1[^>]+>([^<]+)', webpage, 'title', fatal=False),
            'formats': formats,
        }
        # redirect_url = try_get(
        #     metadata,
        #     lambda x: x['props']['initialState']['video']['associatedPlaylists'][0]['videos'][0]['videoAssets'][0]['publicUrl'])
        # m3u8_url = self._request_webpage(HEADRequest(
        #     redirect_url + '?format=redirect&manifest=m3u&format=redirect&Tracking=true&Embedded=true&formats=MPEG4'),
        #     video_id, 'Processing m3u8').url
        # formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        # return {
        #     'url': url,
        #     'id': video_id,
        #     'title': self._search_regex(r'<h1[^>]+>([^<]+)', webpage, 'title', fatal=False),
        #     'formats': formats,
        # }
