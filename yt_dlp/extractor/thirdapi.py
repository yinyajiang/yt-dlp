from .common import InfoExtractor
from .youtube import YoutubeIE
from ..third_api import extract_video_info, parse_api


class ThirdApiIE(InfoExtractor):
    _VALID_URL = r'https?://justtocallthridapi2abcdefghijklmnopqrstuvwxyz\.com.*'
    IE_NAME = 'thirdapi'

    def _real_extract(self, url):
        _, api, data = parse_api(url)
        video_id = None
        youtube_api = 'youtube_rapidapi'
        if api == 'auto':
            api = youtube_api if self._is_youtube_url(url) else ''

        if api == youtube_api:
            video_id = video_id or data.get('__video_id__') or self._youtube_video_id(url)

        return extract_video_info(self, url=url, api=api, video_id=video_id)

    def _youtube_video_id(self, url):
        return self._static_match_id(url, YoutubeIE._VALID_URL)

    def _is_youtube_url(self, url):
        return bool(self._youtube_video_id(url))
