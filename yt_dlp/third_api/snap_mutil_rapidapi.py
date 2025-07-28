from ..cookies import YoutubeDLCookieJar
import random
import time
import os
from hashlib import md5
from ..utils import ExtractorError, remove_query_params, parse_duration, urlencode_postdata
from ._common import is_retry_rsp, is_over_per_second_rsp, RetryError, OverPerSecondError, is_supported_site


#  https://rapidapi.com/tuan2308/api/snap-video3
class SnapMutilRapidApi:
    API_ENDPOINT = 'https://snap-video3.p.rapidapi.com/download'
    API_HOST = 'snap-video3.p.rapidapi.com'
    SUPPORT_SITES = []

    @classmethod
    def is_supported_site(cls, hint):
        return is_supported_site(hint, cls.SUPPORT_SITES)

    def __init__(self, ie):
        self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True)
        if not self._api_keys and os.getenv('rapidapi_key'):
            self._api_keys = [os.getenv('rapidapi_key')]

        self._ie = ie
        if not ie:
            raise ExtractorError('[rapidapi] ie is required')
        if not self._api_keys:
            raise ExtractorError('[rapidapi] api keys is required')

    def extract_video_info(self, video_url, video_id=None):
        video_url = remove_query_params(video_url, ['__force_third_api__', '__third_api__'])

        info = self._get_video_info(video_url)

        if not video_id:
            video_id = md5((info.get('title') or video_url).encode('utf-8')).hexdigest()

        ytb_info = {
            'id': str(video_id),
            'title': info.get('title'),
            'duration': int(parse_duration(info.get('duration'))),
            'thumbnails': [
                {
                    'url': info.get('thumbnail'),
                },
            ],
            'formats': [],
            '_third_api': 'snap_mutil_rapidapi',
        }

        no_video = True
        for media in info.get('medias', []):
            if media.get('videoAvailable') and media.get('audioAvailable'):
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': media.get('quality'),
                })
            elif media.get('videoAvailable') and not media.get('audioAvailable'):
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'acodec': 'none',
                    'format_note': f'{media.get("quality")}(video only)',
                })
            elif media.get('audioAvailable'):
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': 'audio only',
                    'vcodec': 'none',
                    'acodec': media.get('extension'),
                })
            elif not media.get('videoAvailable') and not media.get('audioAvailable'):
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': 'image',
                })
        if no_video and ytb_info.get('formats'):
            ytb_info['_media_type'] = 'PHOTO'
        return ytb_info

    def _get_video_info(self, url):

        def _random_sleep():
            random_sleep = random.randint(0, 1000) / 1000.0
            time.sleep(random_sleep)

        later_count = 0
        for _ in range(500):
            try:
                return self.__get_video_info(url)
            except RetryError:
                later_count += 1
                if later_count > 10:
                    raise
                else:
                    _random_sleep()
                    continue
            except OverPerSecondError:
                _random_sleep()

    def __get_video_info(self, video_url):
        download_json = lambda url, **kwargs: self._ie._download_json(url, 'call-rapidapi', **kwargs)

        info = download_json(self.API_ENDPOINT,
                             data=urlencode_postdata({'url': video_url}),
                             headers={
                                 'x-rapidapi-key': self._api_keys[0],
                                 'x-rapidapi-host': self.API_HOST,
                                 'Content-Type': 'application/x-www-form-urlencoded',
                             },
                             extensions={
                                 'cookiejar': YoutubeDLCookieJar(),
                             },
                             expected_status=lambda _: True,
                             method='POST',
                             )

        empty_medias = False
        if info and not info.get('medias', None):
            if is_retry_rsp(info):
                raise RetryError('error')
            if is_over_per_second_rsp(info):
                raise OverPerSecondError('error')
            empty_medias = True

        if info.get('error'):
            if info.get('message'):
                raise ExtractorError(f'{info.get("message")}, status: {info.get("status")}')
            raise ExtractorError(f'{info.get('error')}')

        if empty_medias:
            raise ExtractorError(str(info))

        return info
