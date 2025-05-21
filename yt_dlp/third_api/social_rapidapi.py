from ..cookies import YoutubeDLCookieJar
import random
import time
import os
import json
from hashlib import md5
from ..utils import ExtractorError, remove_query_params
import urllib.parse
from .common import is_retry_rsp, is_over_per_second_rsp, RetryError, OverPerSecondError


class SocialRapidApi:
    API_ENDPOINT = 'https://auto-download-all-in-one-big.p.rapidapi.com/v1/social/autolink'
    API_HOST = 'auto-download-all-in-one-big.p.rapidapi.com'
    SUPPORT_SITES = [
        # 'Tiktok', 'Douyin', 'Capcut', 'Threads', 'Instagram', 'Facebook', 'Kuaishou', 'Espn',
        # 'Pinterest', 'imdb', 'imgur', 'ifunny', 'Izlesene', 'Reddit', 'Youtube', 'Twitter', 'Vimeo',
        # 'Snapchat', 'Bilibili', 'Dailymotion', 'Sharechat', 'Likee', 'Linkedin', 'Tumblr', 'Hipi',
        # 'Telegram', 'Getstickerpack', 'Bitchute', 'Febspot', '9GAG', 'okeru', 'Rumble', 'Streamable',
        # 'Ted', 'SohuTv', 'Pornbox', 'Xvideos', 'Xnxx', 'Kuaishou', 'Xiaohongshu', 'Ixigua', 'Weibo',
        # 'Miaopai', 'Meipai', 'Xiaoying', 'Yingke', 'Sina', 'Bluesky', 'Soundcloud', 'Mixcloud', 'Spotify',
        # 'Zingmp3', 'Bandcamp',
    ]

    @staticmethod
    def is_supported_site(hint):
        try:
            url = urllib.parse.urlparse(hint)
            if url.netloc:
                hint = url.netloc
        except Exception:
            pass
        if not hint:
            return False
        hint = hint.lower()
        if hint.startswith('www.'):
            hint = hint[4:]
        hint = hint.split(':')[0]
        for s in hint.split('.'):
            if s:
                return s in [site.lower() for site in SocialRapidApi.SUPPORT_SITES]
        return False

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
            'duration': int(info.get('duration') / 1000),
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

        no_video = True
        for media in info.get('medias', []):
            if media.get('type') == 'video':
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': media.get('quality'),
                })
            elif media.get('type') == 'audio':
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': media.get('extension'),
                    'format_note': 'audio only',
                    'vcodec': 'none',
                    'acodec': media.get('extension'),
                })
            elif media.get('type') == 'image':
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

        if info and not info.get('medias', None):
            if is_retry_rsp(info):
                raise RetryError('error')
            if is_over_per_second_rsp(info):
                raise OverPerSecondError('error')

        if info.get('error'):
            if info.get('message'):
                raise ExtractorError(f'{info.get("message")}, status: {info.get("status")}')
            raise ExtractorError('error')
        return info
