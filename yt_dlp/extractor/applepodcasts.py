from .common import InfoExtractor
from ..utils import (
    find_json_by,
    int_or_none,
    parse_iso8601,
)


class ApplePodcastsIE(InfoExtractor):
    _VALID_URL = r'https?://podcasts\.apple\.com/(?:[^/]+/)?podcast(?:/[^/]+){1,2}.*?\bi=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://podcasts.apple.com/us/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/id1135137367?i=1000482637777',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        episode_id = self._match_id(url)
        webpage = self._download_webpage(url, episode_id)
        episode_offer = find_json_by(webpage, 'contextAction', lambda x: str(x['episodeOffer']['contentId']) == str(episode_id) and x['episodeOffer']['streamUrl'], fatal=True)['episodeOffer']
        return {
            'id': episode_id,
            'title': episode_offer.get('title'),
            'formats': [
                {
                    'url': episode_offer.get('streamUrl'),
                },
            ],
            'timestamp': parse_iso8601(episode_offer.get('releaseDateTime')),
            'duration': int_or_none(episode_offer.get('duration')),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
