import urllib.parse

from .common import ExtractorError, InfoExtractor
from ..third_api import InstagramHikerApi, SocialRapidApi, YoutubeRapidApi
from ..utils import unsmuggle_url


class ThirdApiIE(InfoExtractor):
    _VALID_URL = r'https?://justtocallthridapi2abcdefghijklmnopqrstuvwxyz\.com.*'
    IE_NAME = 'thirdapi'

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        api = None
        if data:
            api = data.get('__third_api__')
        if not api:
            parsed = urllib.parse.urlparse(url)
            if parsed.query:
                api = urllib.parse.parse_qs(parsed.query).get('__third_api__', [None])[0]
        if not api:
            raise ExtractorError('must specify api')
        if api == 'social_rapidapi':
            return SocialRapidApi(self).extract_video_info(url)
        elif api == 'youtube_rapidapi':
            return YoutubeRapidApi(self).extract_video_info(url)
        elif api == 'instagram_hikerapi':
            return InstagramHikerApi(self).extract_video_info(url)
        raise ExtractorError(f'unknown api: {api}')
