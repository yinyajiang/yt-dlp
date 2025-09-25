import functools
import json
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    int_or_none,
    join_nonempty,
    parse_qs,
    strip_or_none,
    traverse_obj,
    unified_strdate,
    unified_timestamp,
    update_url_query,
)


class DornaBaseIE(InfoExtractor):
    _LANGS = r'(?:en|it|de|es|fr)'
    _DORNA_DOMAIN = 'https://sso.dorna.com'
    _LANG = None
    _HOST = None
    _SECURE_HOST = None
    _LOGIN_URL = None

    def _perform_login(self, username, password):
        def check_login():
            me = self._download_json(
                f'{self._DORNA_DOMAIN}/api/login/v1/me', None, 'Check Login status',
                expected_status=401)
            return me.get('email') == username

        if check_login():
            return

        webpage, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Downloading login page')
        login_params = parse_qs(urlh.geturl())

        if not login_params.get('client_id'):
            msg = self._search_regex(
                r'(Request unsuccessful\. Incapsula incident ID: \d+-\d+)',
                webpage, 'login_page', fatal=False) or 'Error dowloading login page'
            raise ExtractorError(msg, expected=True)

        data = json.dumps({
            'grant_type': 'password',
            'username': username,
            'password': password,
            'origin_client_id': login_params['client_id'][0],
            'client_id': 'b32ca14f-0709-495a-9184-8bd848cf7e6b',
        }).encode('ascii')
        token = self._download_json(
            f'{self._DORNA_DOMAIN}/api/login/token', None, 'Logging in...', data=data)

        if token.get('token_type') != 'Bearer' or not token.get('access_token'):
            self.report_warning('Error retrieving access token')

        _, urlh = self._download_webpage_handle(
            update_url_query(f'{self._DORNA_DOMAIN}/login/authorize', login_params),
            None, 'Authorization...')

        # if redirects to homepage, login is successful
        if (urlh.geturl().strip('/') not in (self._HOST, self._SECURE_HOST)
                or not check_login()):
            self.report_warning(f'Error finalizing login process: {urlh.geturl()}')

    def _chapters_from_url(self, url):
        if not url:
            return []

        chapters = []
        clips_and_tags = self._download_json(url, None, fatal=False)
        legends = traverse_obj(clips_and_tags, ('videobar', 'legends'))
        clean_legends = {}
        for legend in legends:
            clean_legends[legend['label']] = legend['description']

        for c in traverse_obj(clips_and_tags, ('videobar', 'content')):
            # join various elements to create a title
            # final: EVENT[: RIDER_1[, RIDER_N]]
            # Eg (no riders): "Rain Flag"
            # Eg (1 rider)  : "Crash: Rider_1"
            # Eg (2+ riders): "Overtake: Rider_1, Rider_2"
            chapters.append({
                'title': join_nonempty(
                    clean_legends.get(c['tags'][0]['label']) or 'Misc.',
                    join_nonempty(*[strip_or_none(r['value']) for r in c['riders']], delim=', '),
                    delim=': '),
                'start_time': int(c['timecode']),
                'end_time': int(c['timecode']) + int(c['duration']),
            })
        return chapters

    def _get_motogpapp_data(self, path, request_id):
        return self._download_json(f'{self._SECURE_HOST}/{self._LANG}/motogpapp/{path}/{request_id}', request_id, fatal=False) or {}

    def _get_media_infos(self, video_id, login_method='any'):
        formats = []
        for protocol in ('hls', 'dash'):
            response = self._download_json(
                f'{self._SECURE_HOST}/{self._LANG}/demand/video/{video_id}?protocol={protocol}', video_id, expected_status=(401, 402))

            if response.get('message') in ('User not logged', 'Payment Required'):
                self.raise_login_required(
                    self._search_regex(
                        r'<span class"big">(.+?)</span>', response.get('tpl'),
                        'Login error message', default=response['message']),
                    method=login_method)
            elif response.get('message'):
                raise ExtractorError(response['message'])

            for feed in traverse_obj(response, ('cdns', 0, 'feeds')):
                media_url = traverse_obj(feed, ('protocols', protocol, 'url'))
                if protocol == 'hls':
                    temp_formats = self._extract_m3u8_formats(
                        media_url, f"{video_id}-{feed['label']}", 'mp4', m3u8_id=f"{protocol}-{feed['label']}", fatal=False)
                if protocol == 'dash':
                    temp_formats = self._extract_mpd_formats(
                        media_url, f"{video_id}-{feed['label']}", mpd_id=f"{protocol}-{feed['label']}", fatal=False)

                # set the language for each format
                lang = traverse_obj(feed, ('audio_tracks', 0, 'label'))
                if lang not in ('other'):
                    for fmt in temp_formats:
                        fmt.update({'language': lang})
                formats.extend(temp_formats)

        return {
            'title': strip_or_none(traverse_obj(response, ('video_info', 'title_en'))),
            'alt_title': strip_or_none(traverse_obj(response, ('video_info', 'title'))),
            'thumbnail': traverse_obj(response, ('video_info', 'urlimage')),
            'duration': int_or_none(traverse_obj(response, ('video_info', 'duration'))),
            'formats': formats,
            'chapters': self._chapters_from_url(
                traverse_obj(response, ('video_info', 'clips_and_tags_url'))),
        }


class MotoGPIE(DornaBaseIE):
    # login only works reliably with cookies, usr:psw triggers re-captcha most of the time
    _HOST = 'https://www.motogp.com'
    _SECURE_HOST = 'https://secure.motogp.com'
    _LOGIN_URL = f'{_SECURE_HOST}/en/user/login?return_to={_HOST}'
    _VALID_URL = rf'''(?x)(?:
                              motogp:(?P<lang1>{DornaBaseIE._LANGS}):|
                              (?:{_HOST}|{_SECURE_HOST})/(?P<lang2>{DornaBaseIE._LANGS})/videos/.+/
                          )(?P<id>\d{{5,}})'''
    _TESTS = [{
        # Free video: no account required
        'url': 'https://www.motogp.com/it/videos/2022/12/01/motogp-and-f1-take-centre-stage-as-they-look-to-the-future/445783',
        'only_matching': True,
    }, {
        # Free account required: multi source video (broadcast, helicopter, on-board ...) with chapters
        'url': 'https://www.motogp.com/it/videos/2019/08/11/round-11-motogp-myworld-motorrad-grand-prix-von-osterreich/304604',
        'only_matching': True,
    }, {
        'url': 'motogp:it:304604',
        'only_matching': True,
    }]
    _NETRC_MACHINE = 'motogp'

    def _real_extract(self, url):
        lang1, lang2, video_id = self._match_valid_url(url).group('lang1', 'lang2', 'id')
        self._LANG = lang1 or lang2

        return {
            'id': video_id,
            **self._get_media_infos(video_id, 'cookies'),
        }


class MotoGPGalleryIE(MotoGPIE):
    _VALID_URL = rf'(?:{MotoGPIE._HOST}|{MotoGPIE._SECURE_HOST})/(?P<lang>{DornaBaseIE._LANGS})/video_gallery/.+/(?P<id>\d{{5,}})'
    _TESTS = [{
        'url': 'https://www.motogp.com/en/video_gallery/2022/07/08/behind-the-scenes/429173',
        'only_matching': True,
    }]

    def _get_gallery_data(self, gallery_id):
        data = self._get_motogpapp_data('video/gallery', gallery_id)
        return {
            'title': traverse_obj(data, ('gallery', 'title')),
            'items_id': traverse_obj(data, ('gallery', 'videos', ..., 'nid')),
        }

    def _real_extract(self, url):
        self._LANG, gallery_id = self._match_valid_url(url).groups()
        gallery_data = self._get_gallery_data(gallery_id)
        return self.playlist_result(
            [self.url_result(f'motogp:{self._LANG}:{nid}') for nid in gallery_data.get('items_id')],
            gallery_id, playlist_title=gallery_data.get('title'))


class WorldSBKIE(DornaBaseIE):
    _HOST = 'https://www.worldsbk.com'
    _SECURE_HOST = 'https://secure.worldsbk.com'
    _LOGIN_URL = f'{_SECURE_HOST}/en/user/login?return_to={_HOST}'
    _VALID_URL = rf'(?:{_HOST}|{_SECURE_HOST})/(?P<lang>{DornaBaseIE._LANGS})/videos/(?P<year>\d+)/(?P<id>[^/"?]+)'
    _EMBED_REGEX = [
        rf'<a\s*class="videoplay"\s*href="(?P<url>{_VALID_URL})">',
        rf'href="(?P<url>{_VALID_URL})"\s*class="videoplay"',
    ]
    _TESTS = [{
        # Free account recap video (no chapters, single language)
        'url': 'https://www.worldsbk.com/en/videos/2022/2022%20WorldSBK%20Aragon%20Race%201%20Last%20Lap',
        'only_matching': True,
    }, {
        # Free account with double language audio
        'url': 'https://secure.worldsbk.com/en/videos/2022/2022 WorldSBK Australia Toprak interview',
        'only_matching': True,
    }, {
        # Paying account content with chapters
        'url': 'https://www.worldsbk.com/en/videos/2022/2022 WorldSBK Aragon RACE 1 Full Session',
        'only_matching': True,
    }]

    _NETRC_MACHINE = 'worldsbk'

    def _real_extract(self, url):
        self._LANG, _, display_id = self._match_valid_url(url).groups()
        display_id = urllib.parse.unquote(display_id)

        page = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'<player data-id="(\d+)"', page, 'video_id')
        upload_date = self._search_regex(
            r'<div class="date">(.+?)</div>', page, 'upload_date', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'upload_date': unified_strdate(upload_date),
            'timestamp': unified_timestamp(upload_date),
            **self._get_media_infos(video_id),
        }


class WorldSBKPlaylistIE(WorldSBKIE):
    _VALID_URL = rf'(?:{WorldSBKIE._HOST}|{WorldSBKIE._SECURE_HOST})/{DornaBaseIE._LANGS}/videos/(?P<id>\w+)_videos'
    _TESTS = [{
        'url': 'https://www.worldsbk.com/en/videos/all_videos',
        'only_matching': True,
    }]
    _PAGE_LIMIT = 5
    _PAGE_SIZE = 24
    _LAST_VIDEO_ID = None

    def _fetch_page(self, url, playlist_id, page):
        if self._PAGE_LIMIT == page:
            return {}
        url = f'{url}/ajax/list_{playlist_id}'
        if self._LAST_VIDEO_ID:
            url = f'{url}_before/{self._LAST_VIDEO_ID}'

        page = self._download_json(url, playlist_id)

        for link in re.finditer(
                rf'id="{playlist_id}_videos_(?P<video_id>[\d_]+)"[^/]+href="(?P<video_url>(?:{self._HOST}|{self._SECURE_HOST})/(?:{DornaBaseIE._LANGS})/videos/.+\?from_list={playlist_id}_videos)"',
                page.get('html')):
            self._LAST_VIDEO_ID = link.group('video_id')
            yield self.url_result(link.group('video_url'), ie=WorldSBKIE)

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        entries = OnDemandPagedList(
            functools.partial(self._fetch_page, url, playlist_id),
            self._PAGE_SIZE)

        return self.playlist_result(entries, playlist_id)
