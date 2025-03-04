from datetime import datetime
from ..utils import (
    traverse_obj,
    int_or_none,
    mimetype2codecs,
)
from ..cookies import YoutubeDLCookieJar
import random
import time


def _date_convert(date_str):
    try:
        return datetime.fromisoformat(date_str).strftime('%Y%m%d')
    except Exception:
        return None


class YoutubeRapidApi:
    API_ENDPOINT = 'https://youtube-media-downloader.p.rapidapi.com/v2/video/details'
    API_HOST = 'youtube-media-downloader.p.rapidapi.com'

    def __init__(self, ie):
        self._api_keys = ie._configuration_arg('rapidapi_key', [], casesense=True)
        self._ie = ie
        if not ie:
            raise ValueError('[rapidapi] ie is required')
        if not self._api_keys:
            raise ValueError('[rapidapi] api keys is required')

    def extract_video_info(self, video_id):
        info = self._get_video_info(video_id)

        ytb_info = {
            'id': info.get('id'),
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
            '_third_api': 'rapidapi',
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
                    'id': f'audio-{index} - audio only',
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
                    'id': f"video-{index} (f{video.get('quality')})",
                    **mimetype2codecs(video.get('mimeType'), assign_only_one_codec='both' if video.get('hasAudio') else 'vcodec', acodec_default='none'),
                } for index, video in enumerate(videos)
            ]
            ytb_info['formats'].extend(video_formats)

        return ytb_info

    def _get_video_info(self, video_id):
        for _ in range(500):
            try:
                return self.__get_video_info(video_id)
            except Exception as e:
                if 'per second' not in str(e).lower():
                    raise e
                random_sleep = random.randint(0, 1000) / 1000.0
                time.sleep(random_sleep)

    def __get_video_info(self, video_id):
        download_json = lambda url, **kwargs: self._ie._download_json(url, video_id, **kwargs)
        report_msg = lambda msg: self._ie.report_msg(f'[rapidapi] {msg}')

        first_exception = None
        for key in self._api_keys:
            try:
                url = f'{self.API_ENDPOINT}?videoId={video_id}'
                info = download_json(url, headers={
                    'x-rapidapi-key': key,
                    'x-rapidapi-host': self.API_HOST,
                },
                    extensions={
                    'cookiejar': YoutubeDLCookieJar(),
                },
                    expected_status=lambda _: True,
                )
                if 'status' not in info and 'message' in info:
                    raise Exception(f'{info.get("message")}')
                if not info.get('status'):
                    raise Exception(f'status is not ok, error: {info.get("errorId", "")}, reason: {info.get("reason", "")}')
                return info
            except Exception as e:
                report_msg(f'{e}')
                if not first_exception:
                    first_exception = e
                if any(errorId.lower() in str(e).lower() for errorId in ['per second', 'DRM', 'PaymentRequired', 'MembersOnly', 'LiveStreamOffline', 'RegionUnavailable', 'VideoNotFound']):
                    break
        raise first_exception
