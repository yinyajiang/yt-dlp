from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    join_nonempty,
    traverse_obj,
    url_or_none,
)


class DailyWireBaseIE(InfoExtractor):
    _JSON_PATH = {
        'episode': ('props', 'pageProps', 'episodeData', 'episode'),
        'videos': ('props', 'pageProps', 'videoData', 'video'),
        'podcasts': ('props', 'pageProps', 'episode'),
    }

    def _get_json(self, url):
        sites_type, slug = self._match_valid_url(url).group('sites_type', 'id')
        json_data = self._search_nextjs_data(self._download_webpage(url, slug), slug)
        return slug, traverse_obj(json_data, self._JSON_PATH[sites_type])


class DailyWireIE(DailyWireBaseIE):
    _VALID_URL = r'https?://(?:www\.)dailywire(?:\.com)/(?P<sites_type>episode|videos)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.dailywire.com/episode/1-fauci',
        'info_dict': {
            'id': 'ckzsl50xnqpy30850in3v4bu7',
            'ext': 'mp4',
            'display_id': '1-fauci',
            'title': '1. Fauci',
            'description': 'md5:9df630347ef85081b7e97dd30bc22853',
            'thumbnail': 'https://daily-wire-production.imgix.net/episodes/ckzsl50xnqpy30850in3v4bu7/ckzsl50xnqpy30850in3v4bu7-1648237399554.jpg',
            'creator': 'Caroline Roberts',
            'series_id': 'ckzplm0a097fn0826r2vc3j7h',
            'series': 'China: The Enemy Within',
        },
    }, {
        'url': 'https://www.dailywire.com/episode/ep-124-bill-maher',
        'info_dict': {
            'id': 'cl0ngbaalplc80894sfdo9edf',
            'ext': 'mp3',
            'display_id': 'ep-124-bill-maher',
            'title': 'Ep. 124 - Bill Maher',
            'thumbnail': 'https://daily-wire-production.imgix.net/episodes/cl0ngbaalplc80894sfdo9edf/cl0ngbaalplc80894sfdo9edf-1647065568518.jpg',
            'creator': 'Caroline Roberts',
            'description': 'md5:adb0de584bcfa9c41374999d9e324e98',
            'series_id': 'cjzvep7270hp00786l9hwccob',
            'series': 'The Sunday Special',
        },
    }, {
        'url': 'https://www.dailywire.com/videos/the-hyperions',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug, episode_info = self._get_json(url)
        urls = traverse_obj(
            episode_info, (('segments', 'videoUrl'), ..., ('video', 'audio')), expected_type=url_or_none)

        formats, subtitles = [], {}
        for url in urls:
            if determine_ext(url) != 'm3u8':
                formats.append({'url': url})
                continue
            format_, subs_ = self._extract_m3u8_formats_and_subtitles(url, slug)
            formats.extend(format_)
            self._merge_subtitles(subs_, target=subtitles)
        return {
            'id': episode_info['id'],
            'display_id': slug,
            'title': traverse_obj(episode_info, 'title', 'name'),
            'description': episode_info.get('description'),
            'creator': join_nonempty(('createdBy', 'firstName'), ('createdBy', 'lastName'), from_dict=episode_info, delim=' '),
            'duration': float_or_none(episode_info.get('duration')),
            'is_live': episode_info.get('isLive'),
            'thumbnail': traverse_obj(episode_info, 'thumbnail', 'image', expected_type=url_or_none),
            'formats': formats,
            'subtitles': subtitles,
            'series_id': traverse_obj(episode_info, ('show', 'id')),
            'series': traverse_obj(episode_info, ('show', 'name')),
        }


class DailyWirePodcastIE(DailyWireBaseIE):
    _VALID_URL = r'https?://(?:www\.)dailywire(?:\.com)/(?P<sites_type>podcasts)/(?P<podcaster>[\w-]+/(?P<id>[\w-]+))'
    _TESTS = [{
        'url': 'https://www.dailywire.com/podcasts/morning-wire/get-ready-for-recession-6-15-22',
        'info_dict': {
            'id': 'cl4f01d0w8pbe0a98ydd0cfn1',
            'ext': 'm4a',
            'display_id': 'get-ready-for-recession-6-15-22',
            'title': 'Get Ready for Recession | 6.15.22',
            'description': 'md5:c4afbadda4e1c38a4496f6d62be55634',
            'thumbnail': 'https://daily-wire-production.imgix.net/podcasts/ckx4otgd71jm508699tzb6hf4-1639506575562.jpg',
            'duration': 900.117667,
        },
    }]

    def _real_extract(self, url):
        slug, episode_info = self._get_json(url)
        audio_id = traverse_obj(episode_info, 'audioMuxPlaybackId', 'VUsAipTrBVSgzw73SpC2DAJD401TYYwEp')

        return {
            'id': episode_info['id'],
            'url': f'https://stream.media.dailywire.com/{audio_id}/audio.m4a',
            'display_id': slug,
            'title': episode_info.get('title'),
            'duration': float_or_none(episode_info.get('duration')),
            'thumbnail': episode_info.get('thumbnail'),
            'description': episode_info.get('description'),
        }


class DailyWireShowIE(DailyWireBaseIE):
    _VALID_URL = r'https?://(?:www\.)dailywire(?:\.com)/(?P<sites_type>show)/(?P<id>[\w-]+)'
    _TESTS = [{
        'skip': 'premium only',
        'url': 'https://www.dailywire.com/show/apollo-11-what-we-saw',
        'playlist_mincount': 28,
        'info_dict': {
            'id': 'ckixsvamonvl40862ysxve50i',
            'thumbnail': 'https://daily-wire-production.imgix.net/shows/ckixsvamonvl40862ysxve50i-1679082975554.jpg',
            'title': 'What We Saw',
            'description': 'md5:98d2a7d5cc8175494a4ca611058ed440',
        },
        'params': {
            'skip_download': True,
        },
        'playlist': [{
            'info_dict': {
                'id': 'cltf80tk79fxi0942c7h394b5',
                'season_id': 'what-we-saw-season-3-an-empire-of-terror-season',
                'ext': 'mp4',
                'display_id': 'season-3-an-empire-of-terror',
                'series_id': 'ckixsvamonvl40862ysxve50i',
                'title': 'Season 3: An Empire of Terror',
                'description': 'What We Saw: An Empire of Terror premieres on March 6, 2024.',
                'creators': ['Scott Bowler '],
                'upload_date': '20240306',
                'timestamp': 1709704832,
                'thumbnail': 'https://daily-wire-production.imgix.net/episodes/cltf80tk79fxi0942c7h394b5/cltf80tk79fxi0942c7h394b5-1709694601671.png',
                'series': 'What We Saw',
            }}]
    }]

    def _real_extract(self, url):
        slug = self._match_valid_url(url).group('id')

        show_data = self._call_api(slug, 'getShowBySlug', {'slug': slug})
        if not show_data:
            raise ExtractorError('Show not found')

        for season_data in show_data.get('seasons', []):
            season_data['episodes'] = [
                episode for page in
                self._paginate(season_data.get('slug'), 'getSeasonEpisodes', {'season': {'id': season_data.get('id')}})
                for episode in page
            ]

        return self.playlist_result(
            [self.url_result(f'https://www.dailywire.com/episode/{episode_slug}',
             season_id=season_data.get('slug'), season=season_data.get('title'), url_transparent=True)
             for season_data in show_data.get('seasons', []) for episode_slug in season_data['episodes']],
            show_data.get('id'), show_data.get('name'), show_data.get('description'),
            thumbnail=show_data.get('image'))
