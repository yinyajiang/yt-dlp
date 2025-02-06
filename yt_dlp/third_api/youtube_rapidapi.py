from datetime import datetime
from ..utils import (
    traverse_obj,
    int_or_none,
    mimetype2codecs,
)
from ..cookies import YoutubeDLCookieJar


def _date_convert(date_str):
    try:
        return datetime.fromisoformat(date_str).strftime('%Y%m%d')
    except Exception:
        return None


class YoutubeRapidApi:
    API_ENDPOINT = 'https://youtube-media-downloader.p.rapidapi.com/v2/video/details'
    API_HOST = 'youtube-media-downloader.p.rapidapi.com'

    def __init__(self, api_keys, download_json_func, print_msg_func=None, api_host=API_HOST, api_endpoint=API_ENDPOINT):
        self.api_keys = api_keys
        self.api_host = api_host
        self.api_endpoint = api_endpoint
        self._download_json_func = download_json_func
        self._print_msg_func = print_msg_func

    def get_video_info(self, video_id):
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
        if not self._download_json_func:
            raise ValueError('Download json function not provided')

        first_exception = None
        for key in self.api_keys:
            try:
                url = f'{self.api_endpoint}?videoId={video_id}'
                info = self._download_json_func(url, headers={
                    'x-rapidapi-key': key,
                    'x-rapidapi-host': self.api_host,
                },
                    extensions={
                    'cookiejar': YoutubeDLCookieJar(),
                })
                if not info.get('status'):
                    raise Exception(f'rapidapi video info, status is not ok, error: {info.get("errorId")}')
                return info
            except Exception as e:
                if self._print_msg_func:
                    self._print_msg_func(f'rapidapi error: {e}')
                if not first_exception:
                    first_exception = e
        raise first_exception
