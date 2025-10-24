import urllib.parse

from .extractor import SnapMutilRapidApi, ZMMutilRapidApi, AllInOneMutilRapidApi, YoutubeRapidApi, InstagramHikerApi
from ..utils import unsmuggle_url, ExtractorError
from .mutil import MutilThirdIE


def parse_api(url, api=None):
    url, data = unsmuggle_url(url, {})
    if not api and data:
        api = data.get('__third_api__')
    if not api:
        parsed = urllib.parse.urlparse(url)
        if parsed.query:
            api = urllib.parse.parse_qs(parsed.query).get('__third_api__', [None])[0]
    return url, api, data


def extract_video_info(ie, url, api=None, video_id=None):
    url, api, data = parse_api(url, api)
    if not api or api == 'auto':
        api = AllInOneMutilRapidApi.API_NAME
    if api == ZMMutilRapidApi.API_NAME:
        return ZMMutilRapidApi(ie).extract_video_info(url)
    elif api == YoutubeRapidApi.API_NAME:
        video_id = video_id or data.get('__video_id__')
        if not video_id:
            raise ExtractorError('YoutubeRapidApi use video_id')
        return YoutubeRapidApi(ie).extract_video_info(video_id=video_id)
    elif api == InstagramHikerApi.API_NAME:
        raise ExtractorError('InstagramHikerApi not <extract_video_info> implemented')
    elif api == SnapMutilRapidApi.API_NAME:
        return SnapMutilRapidApi(ie).extract_video_info(url)
    elif api == AllInOneMutilRapidApi.API_NAME:
        return AllInOneMutilRapidApi(ie).extract_video_info(url)
    elif api == MutilThirdIE.API_NAME or api == 'mutil_rapidapi':
        return MutilThirdIE(ie).extract_video_info(url)
    raise ExtractorError(f'unknown api: {api}')
