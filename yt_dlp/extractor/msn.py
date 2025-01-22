
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    determine_is_know_media_ext,
    int_or_none,
    traverse_obj,
    unescapeHTML,
)


class MSNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|preview)\.)?msn\.com/(?P<locale>[^/]+)/(?:[^/]+/)*(?P<display_id>[^/]+)/[a-z]{2}-(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.msn.com/en-in/money/video/7-ways-to-get-rid-of-chest-congestion/vi-BBPxU6d',
        'only_matching': True,
    }, {
        # Article, multiple Dailymotion Embeds
        'url': 'https://www.msn.com/en-in/money/sports/hottest-football-wags-greatest-footballers-turned-managers-and-more/ar-BBpc7Nl',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/news/offbeat/meet-the-nine-year-old-self-made-millionaire/ar-BBt6ZKf',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/video/watch/obama-a-lot-of-people-will-be-disappointed/vi-AAhxUMH',
        'only_matching': True,
    }, {
        # geo restricted
        'url': 'http://www.msn.com/en-ae/foodanddrink/joinourtable/the-first-fart-makes-you-laugh-the-last-fart-makes-you-cry/vp-AAhzIBU',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/entertainment/bollywood/watch-how-salman-khan-reacted-when-asked-if-he-would-apologize-for-his-‘raped-woman’-comment/vi-AAhvzW6',
        'only_matching': True,
    }, {
        # Vidible(AOL) Embed
        'url': 'https://www.msn.com/en-us/money/other/jupiter-is-about-to-come-so-close-you-can-see-its-moons-with-binoculars/vi-AACqsHR',
        'only_matching': True,
    }, {
        # Dailymotion Embed
        'url': 'https://www.msn.com/es-ve/entretenimiento/watch/winston-salem-paire-refait-des-siennes-en-perdant-sa-raquette-au-service/vp-AAG704L',
        'only_matching': True,
    }, {
        # YouTube Embed
        'url': 'https://www.msn.com/en-in/money/news/meet-vikram-%E2%80%94-chandrayaan-2s-lander/vi-AAGUr0v',
        'only_matching': True,
    }, {
        # NBCSports Embed
        'url': 'https://www.msn.com/en-us/money/football_nfl/week-13-preview-redskins-vs-panthers/vi-BBXsCDb',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        locale, display_id, page_id = self._match_valid_url(url).groups()
        items_list = []
        try:
            js = self._download_json(f'https://assets.msn.com/content/view/v2/Detail/{locale}/{page_id}', display_id)
            if not js:
                raise ExtractorError(f'download json failed: https://assets.msn.com/content/view/v2/Detail/{locale}/{page_id}')
        except Exception as e:
            if any(status in str(e) for status in ['410', '404']):
                raise ExtractorError(f'this video is not available, {e}')
            raise e

        if isinstance(js, list):
            items_list = js
        else:
            items_list.append(js)

        entries = []
        for index, item in enumerate(items_list):
            if not item:
                continue
            provider_id = traverse_obj(item, ('provider', 'id', {str}), default='')
            player_name = traverse_obj(item, ('provider', 'name', {str}), default='')
            if player_name and provider_id:
                entry = None
                if player_name == 'AOL':
                    if provider_id.startswith('http'):
                        provider_id = self._search_regex(
                            r'https?://delivery\.vidible\.tv/video/redirect/([0-9a-f]{24})',
                            provider_id, 'vidible id')
                    entry = self.url_result(
                        'aol-video:' + provider_id, 'Aol', provider_id)
                elif player_name == 'Dailymotion':
                    entry = self.url_result(
                        'https://www.dailymotion.com/video/' + provider_id,
                        'Dailymotion', provider_id)
                elif player_name == 'YouTube':
                    entry = self.url_result(
                        provider_id, 'Youtube', provider_id)
                elif player_name == 'NBCSports':
                    entry = self.url_result(
                        'http://vplayer.nbcsports.com/p/BxmELC/nbcsports_embed/select/media/' + provider_id,
                        'NBCSportsVPlayer', provider_id)
                if entry:
                    entries.append(entry)
                    continue

            title = item.get('title') or display_id
            video_id = item.get('id') or f'{display_id}_{index}'
            thumbnails = []
            if traverse_obj(item, ('thumbnail', 'image', 'url'), default=None):
                thumbnails = [{
                    'width': traverse_obj(item, ('thumbnail', 'image', 'width'), default=None),
                    'height': traverse_obj(item, ('thumbnail', 'image', 'height'), default=None),
                    'url': traverse_obj(item, ('thumbnail', 'image', 'url'), default=None),
                }]
            if not thumbnails:
                for image in traverse_obj(item, ('imageResources', {list}), default=[]):
                    if image.get('url'):
                        thumbnails.append({
                            'width': image.get('width', None),
                            'height': image.get('height', None),
                            'url': image.get('url'),
                            'preference': image.get('quality', None),
                        })

            formats = []
            for file_ in traverse_obj(item, ('videoMetadata', 'externalVideoFiles', {list}), default=[]):
                format_url = file_.get('url')
                if not format_url:
                    continue
                format_url_ext = determine_ext(format_url, 'm3u8')

                if format_url_ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, display_id, 'mp4',
                        m3u8_id='hls', fatal=False))
                elif format_url_ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        format_url, display_id, 'dash', fatal=False))
                elif format_url_ext == 'ism':
                    if format_url.endswith('.ism'):
                        format_url += '/manifest'
                    formats.extend(self._extract_ism_formats(
                        format_url, display_id, 'mss', fatal=False))
                else:
                    format_id = file_.get('format', 'mp4')
                    format_file_size = int_or_none(file_.get('fileSize'))
                    video_format = {
                        'url': format_url,
                        'ext': format_url_ext,
                        'format_id': format_id,
                        'width': int_or_none(file_.get('width')),
                        'height': int_or_none(file_.get('height')),
                        'quality': 1 if format_id == '1001' else None,
                    }
                    if format_file_size:
                        video_format['filesize'] = format_file_size
                    formats.append(video_format)
            if not formats:
                sourceHref = item.get('sourceHref')
                if sourceHref and determine_is_know_media_ext(sourceHref):
                    formats.append({
                        'url': sourceHref,
                        'ext': determine_ext(sourceHref),
                        'format_id': 'source_href',
                    })
            if not formats and thumbnails:
                formats.append({
                    'url': thumbnails[0].get('url'),
                    'ext': 'jpg',
                    'width': thumbnails[0].get('width'),
                    'height': thumbnails[0].get('height'),
                    'vcodec': 'jpg',
                    'format_id': 'image',
                    '_media_type': 'PHOTO',
                })

            entries.append({
                'id': video_id,
                'title': title,
                'description': traverse_obj(item, ('abstract'), default=None),
                'thumbnails': thumbnails,
                'uploader_id': provider_id,
                'formats': formats,
                'uploader': item.get('createdBy', None),
            })

        if not entries:
            webpage = self._download_webpage(url, display_id)
            error = unescapeHTML(self._search_regex(
                r'data-error=(["\'])(?P<error>.+?)\1',
                webpage, 'error', group='error'))
            raise ExtractorError(f'{self.IE_NAME} said: {error}', expected=True)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, page_id)
