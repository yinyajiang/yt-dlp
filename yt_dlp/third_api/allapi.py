import urllib.parse

from .extractor import SnapMutilRapidApi, ZMMutilRapidApi, AllInOneMutilRapidApi, YoutubeRapidApi
from ..utils import unsmuggle_url, ExtractorError
from .mutil import MutilThirdIE


def extract_video_info(ie, url, api=None):
    url, data = unsmuggle_url(url, {})
    if not api and data:
        api = data.get('__third_api__')
    if not api:
        parsed = urllib.parse.urlparse(url)
        if parsed.query:
            api = urllib.parse.parse_qs(parsed.query).get('__third_api__', [None])[0]
    if not api:
        raise ExtractorError('must specify api')
    if api == 'zm_rapidapi':
        return ZMMutilRapidApi(ie).extract_video_info(url)
    elif api == 'youtube_rapidapi':
        video_id = data.get('__video_id__')
        if not video_id:
            raise ExtractorError('youtube_rapidapi use video_id')
        return YoutubeRapidApi(ie).extract_video_info(video_id=video_id)
    elif api == 'instagram_hikerapi':
        raise ExtractorError('instagram_hikerapi not <extract_video_info> implemented')
    elif api == 'snap_mutil_rapidapi':
        return SnapMutilRapidApi(ie).extract_video_info(url)
    elif api == 'allinone_mutil_rapidapi':
        return AllInOneMutilRapidApi(ie).extract_video_info(url)
    elif api == 'mutil_api' or api == 'mutil_rapidapi':
        return MutilThirdIE(ie).extract_video_info(url)
    raise ExtractorError(f'unknown api: {api}')
