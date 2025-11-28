from .common import InfoExtractor
from .youtube import YoutubeIE
from ..third_api import extract_video_info


class ThirdApiIE(InfoExtractor):
    _VALID_URL = r'https?://7383abbe948a410fb1b42ae8ca7660d4\.com.*'
    IE_NAME = 'thirdapi'

    def _real_extract(self, url):
        return extract_video_info(self, url=url)

    def _youtube_video_id(self, url):
        return self._static_match_id(url, YoutubeIE._VALID_URL)

    def _is_youtube_url(self, url):
        return bool(self._youtube_video_id(url))
