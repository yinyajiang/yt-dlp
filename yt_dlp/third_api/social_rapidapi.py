from ..cookies import YoutubeDLCookieJar
import random
import time
import os
import json
from hashlib import md5
from ..utils import ExtractorError, remove_query_params


class SocialRapidApi:
    API_ENDPOINT = 'https://auto-download-all-in-one-big.p.rapidapi.com/v1/social/autolink'
    API_HOST = 'auto-download-all-in-one-big.p.rapidapi.com'

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
            'id': video_id,
            'title': info.get('title'),
            'duration': info.get('duration') / 1000,
            'channel': info.get('author'),
            'uploader': info.get('author'),
            'thumbnails': [
                {
                    'url': info.get('thumbnail'),
                },
            ],
            'formats': [],
            '_third_api': 'rapidapi',
        }

        for media in info.get('medias', []):
            if media.get('type') == 'video':
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': media.get('quality'),
                })
            elif media.get('type') == 'audio':
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': 'audio only',
                    'vcodec': 'none',
                    'acodec': media.get('extension'),
                })

        return ytb_info

    def _get_video_info(self, video_id):

        def _random_sleep():
            random_sleep = random.randint(0, 1000) / 1000.0
            time.sleep(random_sleep)

        later_count = 0
        for _ in range(500):
            try:
                return self.__get_video_info(video_id)
            except Exception as e:
                msg = str(e).lower()
                if 'please try again later' in msg:
                    later_count += 1
                    if later_count > 10:
                        raise e
                    else:
                        _random_sleep()
                        continue

                if 'per second' not in msg:
                    raise e
                _random_sleep()

    def __get_video_info(self, video_url):
        download_json = lambda url, **kwargs: self._ie._download_json(url, 'call-rapidapi', **kwargs)

        info = download_json(self.API_ENDPOINT,
                             data=json.dumps({'url': video_url}).encode('utf-8'),
                             headers={
                                 'x-rapidapi-key': self._api_keys[0],
                                 'x-rapidapi-host': self.API_HOST,
                                 'Content-Type': 'application/json',
                             },
                             extensions={
                                 'cookiejar': YoutubeDLCookieJar(),
                             },
                             expected_status=lambda _: True,
                             )
        if info.get('error'):
            if info.get('message'):
                raise ExtractorError(f'{info.get("message")}, status: {info.get("status")}')
            raise ExtractorError('error')
        return info
