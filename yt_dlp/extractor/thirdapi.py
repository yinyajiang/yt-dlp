from .common import InfoExtractor
from .youtube import YoutubeIE
from ..third_api import extract_video_info, parse_api


class ThirdApiIE(InfoExtractor):
    _VALID_URL = r'https?://justtocallthridapi2abcdefghijklmnopqrstuvwxyz\.com.*'
    IE_NAME = 'thirdapi'

    def _real_extract(self, url):
        _, api, data = parse_api(url)
        if api == 'youtube_rapidapi':
            video_id = data.get('__video_id__')
            if not video_id:
                video_id = self._static_match_id(url, YoutubeIE._VALID_URL)

        return extract_video_info(self, url=url, api=api, video_id=video_id)
