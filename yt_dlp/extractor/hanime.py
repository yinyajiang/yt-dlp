from __future__ import annotations

from .common import InfoExtractor
from ..utils import traverse_obj, url_or_none

_HANIME_BASE_URL: str = 'https://hanime.tv'


class HanimeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.tv/videos/hentai/(?P<id>[a-z-0-9]+)'
    _TRY_GENERIC = True
    _TESTS = [{
        'url': f'{_HANIME_BASE_URL}/videos/hentai/jewelry-1',
        'only_matching': True,
    }]

    def _get_formats(self, video_id, _streams: list[dict]) -> list[dict] | None:
        if not _streams:
            raise Exception('No streams found')

        _streams = [stream for stream in _streams if stream.get('is_guest_allowed')]
        if not _streams:
            raise Exception('streams are not public')

        fmts = []
        for stream in _streams:
            if '.m3u8' in stream.get('url'):
                m3u8_fmts = self._extract_m3u8_formats(stream.get('url'), video_id, 'mp4', fatal=False)
                if len(m3u8_fmts) == 1 and 'width' in stream and 'height' in stream:
                    m3u8_fmts[0]['width'] = int(stream['width'])
                    m3u8_fmts[0]['height'] = int(stream['height'])
                fmts.extend(m3u8_fmts)
            else:
                fmts.append({
                    'url': stream.get('url'),
                    'width': int(stream.get('width')),
                    'height': int(stream.get('height')),
                    'format_id': stream.get('slug'),
                    'filesize_approx': int(stream.get('filesize_mbs', 0) * 1024 ** 2),
                })
        if not fmts:
            raise Exception('No formats found')
        return fmts

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta: dict = self._download_json(f'{_HANIME_BASE_URL}/api/v8/video?id={video_id}', video_id=video_id)
        streams: list = traverse_obj(meta, ('videos_manifest', 'servers', 0, 'streams'), expected_type=list, default=[])

        return {
            'id': video_id,
            'title': traverse_obj(meta, ('hentai_video', 'name'), expected_type=str),
            'thumbnail': traverse_obj(meta, ('hentai_video', 'poster_url'), expected_type=url_or_none, default=None),
            'uploader': traverse_obj(meta, ('brand', 'title'), expected_type=str, default=None),
            'formats': self._get_formats(video_id, streams),
        }
