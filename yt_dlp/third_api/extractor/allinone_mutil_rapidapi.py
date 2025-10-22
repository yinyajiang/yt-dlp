from ...cookies import YoutubeDLCookieJar
import random
import time
from hashlib import md5
from ...utils import ExtractorError, mimetype2codecs
import json
from .common import is_retry_rsp, is_over_per_second_rsp, RetryError, OverPerSecondError, is_supported_site, remove_third_api_params


#  https://rapidapi.com/manhgdev/api/download-all-in-one-lite
class AllInOneMutilRapidApi:
    API_ENDPOINT = 'https://download-all-in-one-lite.p.rapidapi.com/autolink'
    API_HOST = 'download-all-in-one-lite.p.rapidapi.com'
    SUPPORT_SITES = [
        'Tiktok', 'Douyin', 'Capcut', 'Threads', 'Instagram', 'Facebook', 'Kuaishou', 'Espn',
        'Pinterest', 'imdb', 'imgur', 'ifunny', 'Izlesene', 'Reddit', 'Youtube', 'Twitter', 'Vimeo',
        'Snapchat', 'Bilibili', 'Dailymotion', 'Sharechat', 'Likee', 'Linkedin', 'Tumblr', 'Hipi',
        'Telegram', 'Getstickerpack', 'Bitchute', 'Febspot', '9GAG', 'okeru', 'Rumble', 'Streamable',
        'Ted', 'SohuTv', 'Pornbox', 'Xvideos', 'Xnxx', 'Kuaishou', 'Xiaohongshu', 'Ixigua', 'Weibo',
        'Miaopai', 'Meipai', 'Xiaoying', 'Yingke', 'Sina', 'Bluesky', 'Soundcloud', 'Mixcloud', 'Spotify',
        'Zingmp3', 'Bandcamp', 'X', 'akillitv',
    ]

    @classmethod
    def is_supported_site(cls, hint):
        return is_supported_site(hint, cls.SUPPORT_SITES)

    def __init__(self, ie):
        self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True, enable_env=True)
        if not self._api_keys:
            self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True, ie_key='youtube')
        self._ie = ie
        if not ie:
            raise ExtractorError('[rapidapi] ie is required')
        if not self._api_keys:
            raise ExtractorError('[rapidapi] api keys is required')

    def extract_video_info(self, video_url, video_id=None):
        video_url = remove_third_api_params(video_url)

        info = self._get_video_info(video_url)

        if not video_id:
            video_id = info.get('id') or md5((info.get('title') or video_url).encode('utf-8')).hexdigest()

        ytb_info = {
            'id': str(video_id),
            'title': info.get('title'),
            'duration': int(info.get('duration')),
            'thumbnails': [
                {
                    'url': info.get('thumbnail'),
                },
            ],
            'formats': [],
            '_third_api': 'allinone_mutil_rapidapi',
        }

        has_is_audio_field = any('is_audio' in media for media in info.get('medias', []))

        no_video = True
        for media in info.get('medias', []):
            ext = media.get('extension')
            tbr = (media.get('bitrate', 0) / 1000) or None
            file_size = media.get('data_size') or None
            if media.get('type') == 'video' and (not has_is_audio_field or media.get('is_audio')):
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': ext,
                    'filesize': file_size,
                    'format_note': media.get('quality'),
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'fps': media.get('fps'),
                    'tbr': tbr,
                    'vbr': tbr,
                    **mimetype2codecs(media.get('mimeType'), assign_only_one_codec=None, vcodec_default=ext, acodec_default=ext),
                })
            elif media.get('type') == 'video' and (has_is_audio_field and not media.get('is_audio')):
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': ext,
                    'filesize': file_size,
                    'format_note': f'{media.get("quality")}(video only)',
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'fps': media.get('fps'),
                    'tbr': tbr,
                    'vbr': tbr,
                    **mimetype2codecs(media.get('mimeType'), assign_only_one_codec='vcodec', vcodec_default=ext),
                    'acodec': 'none',
                })
            elif media.get('type') == 'audio':
                no_video = False
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': ext,
                    'filesize': file_size,
                    'format_note': 'audio only',
                    'tbr': tbr,
                    'abr': tbr,
                    **mimetype2codecs(media.get('mimeType'), assign_only_one_codec='acodec', acodec_default=ext),
                    'vcodec': 'none',
                })
            elif media.get('type') == 'image':
                ytb_info['formats'].append({
                    'url': media.get('url'),
                    'ext': ext,
                    'filesize': file_size,
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
            raise ExtractorError(f'{info.get("error")}')

        if empty_medias:
            raise ExtractorError(str(info))

        return info
