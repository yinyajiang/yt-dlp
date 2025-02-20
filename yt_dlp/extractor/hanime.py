from __future__ import annotations

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    str_or_none,
    traverse_obj,
    try_get,
    url_or_none,
)


class HanimetvBaseIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<host>(?:www\.)?(?:members\.)?hanime\.tv)/videos/hentai/(?P<id>[a-zA-Z0-9-]+)'
    _TRY_GENERIC = True
    _TESTS = [
        {
            'url': 'https://hanime.tv/videos/hentai/jewelry-1',
            'only_matching': True,
        },
        {
            'url': 'https://hanime.tv/videos/hentai/enjo-kouhai-1',
            'only_matching': True,
        }, {
            'url': 'https://hanime.tv/videos/hentai/enjo-kouhai-2',
            'only_matching': True,
        }, {
            'url': 'https://hanime.tv/videos/hentai/enjo-kouhai-3',
            'only_matching': True,
        }, {
            'url': 'https://hanime.tv/videos/hentai/chizuru-chan-kaihatsu-nikki-1',
            'only_matching': True,
        }, {
            'url': 'https://hanime.tv/videos/hentai/chizuru-chan-kaihatsu-nikki-2',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        try:
            host = self._match_valid_url(url).group('host')
            return self._extract_by_api(host, video_id)
        except Exception:
            pass

        webpage = self._download_webpage(url, video_id)
        json_data = self._html_search_regex(r'window.__NUXT__=(.+?);<\/script>', webpage, 'Hanime.tv Inline JSON', fatal=True)
        json_data = self._parse_json(json_data, video_id)['state']['data']['video']
        server_data_dict = json_data['videos_manifest']['servers']
        url_list = []
        for server in range(len(server_data_dict)):
            for stream in range(len(server_data_dict[server]['streams'])):
                stream_data_dict = server_data_dict[server]['streams']
                if len(url_list) == len(stream_data_dict):
                    break
                else:
                    tmp_list = {
                        'url': stream_data_dict[stream]['url'],
                        'width': int_or_none(stream_data_dict[stream]['width']),
                        'height': int_or_none(stream_data_dict[stream]['height']),
                    }

                    url_list.append(tmp_list)

        url_list = sorted(url_list, key=lambda val: val['width'] * val['height'])
        title = json_data['hentai_video']['name'] or video_id
        alt_title = try_get(json_data, lambda val: val['hentai_video']['titles'][0]['title'])
        description = clean_html(try_get(json_data, lambda val: val['hentai_video']['description']))
        publisher = try_get(json_data, lambda val: val['hentai_video']['brand'])
        tags = []
        tag_dict = try_get(json_data, lambda val: val['hentai_video']['hentai_tags'])
        if tag_dict:
            for i in range(len(tag_dict)):
                tags.append(try_get(tag_dict, lambda val: val[i]['text'], str))

        formats = []

        for i in range(len(url_list)):
            if not url_list[i].get('url'):
                continue

            if '.m3u8' in url_list[i]['url']:
                formats.extend(self._extract_m3u8_formats(url_list[i]['url'], video_id, 'mp4', fatal=False))
                continue

            formats.append(
                {
                    'url': url_list[i]['url'],
                    'width': url_list[i].get('width'),
                    'height': url_list[i].get('height'),
                    'resolution': str_or_none(url_list[i]['width']) + 'x' + str_or_none(url_list[i]['height']),
                    'container': 'mp4',
                    'ext': 'mp4',
                    'protocol': 'm3u8',
                    'preference': 1 if url_list[i]['height'] == 720 else None,
                })

        self._remove_duplicate_formats(formats)
        self._sort_formats(formats)
        return {
            'id': video_id,
            'formats': formats,
            'description': description,
            'creator': publisher,
            'title': title,
            'alt_title': alt_title,
            'tags': tags,
            'release_date': try_get(json_data, lambda val: val['hentai_video']['released_at'][:10].replace('-', '')),
            'timestamp': try_get(json_data, lambda val: val['hentai_video']['released_at_unix']),
            'view_count': try_get(json_data, lambda val: val['hentai_video']['views']),
            'like_count': try_get(json_data, lambda val: val['hentai_video']['likes']),
            'dislike_count': try_get(json_data, lambda val: val['hentai_video']['dislikes']),
            'age_limit': 18,
        }

    def _extract_by_api(self, host, video_id):
        meta: dict = self._download_json(f'https://{host}/api/v8/video?id={video_id}', video_id=video_id)
        streams: list = traverse_obj(meta, ('videos_manifest', 'servers', 0, 'streams'), expected_type=list, default=[])
        if not streams:
            raise Exception('No streams found')

        streams = [stream for stream in streams if stream.get('is_guest_allowed')]
        if not streams:
            raise Exception('streams are not public')

        fmts = []
        for stream in streams:
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
        return {
            'id': video_id,
            'title': traverse_obj(meta, ('hentai_video', 'name'), expected_type=str),
            'thumbnail': traverse_obj(meta, ('hentai_video', 'poster_url'), expected_type=url_or_none, default=None),
            'uploader': traverse_obj(meta, ('brand', 'title'), expected_type=str, default=None),
            'formats': fmts,
        }


class HanimetvPlaylistIE(HanimetvBaseIE):
    _VALID_URL = r'https?://(?P<host>(?:www\.)?(?:members\.)?hanime\.tv)/videos/hentai/(?P<vid>.+)\?playlist_id=(?P<id>[a-zA-Z0-9-]+)'

    def _extract_entries(self, url, item_id, title):
        return [
            self.url_result(
                url,
                HanimetvBaseIE.ie_key(), video_id=item_id,
                video_title=title),
        ]

    def _entries(self, url, host, playlist_id):
        base_url = f'https://{host}/videos/hentai/%s'
        base_playlist_url = f'{base_url}?playlist_id=%s'
        mobj = re.match(self._VALID_URL, url)
        curr_vid_id = mobj.group('vid')
        curr_vid = url
        first_video_id = curr_vid_id
        seek_next_vid = True
        interation_count = 1
        while (seek_next_vid):
            webpage = self._download_webpage(curr_vid, curr_vid_id, note='Downloading webpage: %s' % curr_vid)

            json_data = self._html_search_regex(r'window.__NUXT__=(.+?);<\/script>', webpage, 'Hanime.tv Inline JSON')
            json_data = self._parse_json(json_data, curr_vid_id)['state']['data']['video']
            curr_vid_id = json_data['hentai_video']['slug']
            curr_vid_url = base_url % curr_vid_id
            webpage = None

            if curr_vid_id != first_video_id or interation_count == 1:
                yield from self._extract_entries(curr_vid_url, interation_count, curr_vid_id)

                try:
                    next_vid_id = json_data['next_hentai_video']['slug']
                    next_vid_url = base_playlist_url % (next_vid_id, playlist_id)
                    curr_vid = next_vid_url
                except AttributeError:
                    seek_next_vid = False

                interation_count += 1

            else:
                seek_next_vid = False

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        playlist_id = mobj.group('id')
        self.to_screen(self._entries(url, host, playlist_id))
        return self.playlist_result(self._entries(url, host, playlist_id), playlist_id)
