from datetime import datetime
from ...utils import (
    traverse_obj,
    int_or_none,
    mimetype2codecs,
    ExtractorError,
)
from ...cookies import YoutubeDLCookieJar
import random
import time
from .common import is_retry_rsp, is_over_per_second_rsp, RetryError, OverPerSecondError


def _date_convert(date_str):
    try:
        return datetime.fromisoformat(date_str).strftime('%Y%m%d')
    except Exception:
        return None

# https://rapidapi.com/DataFanatic/api/youtube-media-downloader


class YoutubeRapidApi:
    API_ENDPOINT = 'https://youtube-media-downloader.p.rapidapi.com/v2/video/details'
    API_HOST = 'youtube-media-downloader.p.rapidapi.com'
    API_NAME = 'youtube_rapidapi'

    def __init__(self, ie):
        self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True, enable_env=True)
        if not self._api_keys:
            self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True, ie_key='youtube')

        self._ie = ie
        if not ie:
            raise ExtractorError('[rapidapi] ie is required')
        if not self._api_keys:
            raise ExtractorError('[rapidapi] api keys is required')

    def extract_video_info(self, video_id):
        info = self._get_video_info(video_id)

        ytb_info = {
            'id': str(info.get('id')),
            'title': info.get('title'),
            'description': info.get('description'),
            'duration': info.get('lengthSeconds'),
            'view_count': info.get('viewCount'),
            'like_count': info.get('likeCount'),
            'channel_id': traverse_obj(info, ('channel', 'id'), default=None),
            'channel_url': 'https://www.youtube.com/channel/' + traverse_obj(info, ('channel', 'id'), default=''),
            'channel': traverse_obj(info, ('channel', 'name'), default=None),
            'uploader': traverse_obj(info, ('channel', 'id'), default=None),
            'uploader_id': traverse_obj(info, ('channel', 'handle'), default=None),
            'uploader_url': 'https://www.youtube.com/' + traverse_obj(info, ('channel', 'handle'), default=''),
            'upload_date': _date_convert(info.get('publishedTime')),
            'is_live': info.get('isLiveNow'),
            'was_live': info.get('isLiveStream'),
            'comment_count': int_or_none(info.get('commentCountText')),
            'thumbnails': info.get('thumbnails'),
            'formats': [],
            'subtitles': {},
            '_params': {
                'proxy': '__noproxy__',
            },
            '_third_api': 'youtube_rapidapi',
        }

        if subtitles_ := traverse_obj(info, ('subtitles', 'items'), default=None):
            for subtitle in subtitles_:
                ytb_info['subtitles'][subtitle.get('code')] = [
                    {
                        'ext': ext,
                        'url': f"{subtitle.get('url')}&fmt={ext}",
                        'name': subtitle.get('text'),
                    }
                    for ext in ['json3', 'srv1', 'srv2', 'srv3', 'ttml', 'vtt']
                ]

        if audios := traverse_obj(info, ('audios', 'items'), default=None):
            audio_formats = [
                {
                    'url': audio.get('url'),
                    'ext': audio.get('extension'),
                    'filesize': audio.get('size'),
                    'format_note': 'audio only',
                    **mimetype2codecs(audio.get('mimeType'), assign_only_one_codec='acodec'),
                    'vcodec': 'none',
                } for index, audio in enumerate(audios)
            ]
            ytb_info['formats'].extend(audio_formats)

        if videos := traverse_obj(info, ('videos', 'items'), default=None):
            video_formats = [
                {
                    'url': video.get('url'),
                    'ext': video.get('extension'),
                    'filesize': video.get('size'),
                    'width': video.get('width'),
                    'height': video.get('height'),
                    'format_note': video.get('quality'),
                    **mimetype2codecs(video.get('mimeType'), assign_only_one_codec='both' if video.get('hasAudio') else 'vcodec', acodec_default='none'),
                } for index, video in enumerate(videos)
            ]
            ytb_info['formats'].extend(video_formats)

        return ytb_info

    def _get_video_info(self, video_id):

        def _random_sleep():
            random_sleep = random.randint(0, 1000) / 1000.0
            time.sleep(random_sleep)

        later_count = 0
        for _ in range(500):
            try:
                return self.__get_video_info(video_id)
            except RetryError:
                later_count += 1
                if later_count > 10:
                    raise
                else:
                    _random_sleep()
                    continue
            except OverPerSecondError:
                _random_sleep()

    def __get_video_info(self, video_id):

        download_json = lambda url, **kwargs: self._ie._download_json(url, video_id, **kwargs)

        url = f'{self.API_ENDPOINT}?videoId={video_id}&urlAccess=normal&videos=auto&audios=auto'
        info = download_json(url, headers={
            'x-rapidapi-key': self._api_keys[0],
            'x-rapidapi-host': self.API_HOST,
        },
            extensions={
            'cookiejar': YoutubeDLCookieJar(),
        },
            expected_status=lambda _: True,
        )

        if traverse_obj(info, ('videos', 'items'), default=None):
            return info
        if traverse_obj(info, ('audios', 'items'), default=None):
            return info

        if info and not info.get('videos', None) and not info.get('audios', None):
            if is_retry_rsp(info):
                raise RetryError('error')
            if is_over_per_second_rsp(info):
                raise OverPerSecondError('error')

        def __get_error(node):
            if not node:
                return None
            errorId = node.get('errorId', None)
            if errorId and errorId.lower() != 'success':
                return f'{errorId}, {node.get("reason", "error")}'
            return None

        rootError = __get_error(info)
        videosError = __get_error(info.get('videos', {}))
        audiosError = __get_error(info.get('audios', {}))
        error = rootError or videosError
        if error:
            raise ExtractorError(f'{error}')
        if not info.get('videos', None) and audiosError:
            raise ExtractorError(f'{audiosError}')
        return info
