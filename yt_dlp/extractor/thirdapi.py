from .common import InfoExtractor
from ..third_api import extract_video_info


class ThirdApiIE(InfoExtractor):
    _VALID_URL = r'https?://justtocallthridapi2abcdefghijklmnopqrstuvwxyz\.com.*'
    IE_NAME = 'thirdapi'

    def _real_extract(self, url):
        return extract_video_info(self, url)
