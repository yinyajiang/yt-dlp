
from .common import InfoExtractor
from ..utils import determine_is_know_media_ext, str_to_int


class Rule34XXXIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rule34\.xxx/(?:index.php)?\?(?=.*page=post)(?=.*s=view)(?=.*id=(?P<id>\d+))'
    _TRY_GENERIC = True
    _TESTS = [
        {
            'url': 'https://rule34.xxx/index.php?page=post&s=view&id=4328926',
            'md5': '5b21e7ba114d023b6f455919ddeafbe9',
            'info_dict': {
                'id': '4328926',
                'ext': 'mp4',
                'title': 'rule34xxx',
                'url': r're:^https://.*\.rule34\.xxx/.*\.mp4',
                'width': 1920,
                'height': 1080,
                'thumbnail': r're:https://.*\.rule34\.xxx/thumbnails/.*\.jpg',
                'age_limit': 18,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._og_search_property('image', webpage)
        if not determine_is_know_media_ext(video_url):
            raise Exception('Unknown media extension')
        title = self._generic_title(url, webpage, default='rule34xxx')
        width = str_to_int(self._html_search_regex(r'\'width\':\s*(\d+)', webpage, 'width', default=None, fatal=False))
        height = str_to_int(self._html_search_regex(r'\'height\':\s*(\d+)', webpage, 'height', default=None, fatal=False))
        thumbnails = None
        if thumbnail := self._html_search_regex(r'(https://.*\.rule34\.xxx/thumbnails/[^\?"\']+)', webpage, 'thumbnail', default=None, fatal=False):
            thumbnails = [
                {
                    'url': thumbnail,
                },
            ]
        return {
            'id': video_id,
            'formats': [{
                'url': video_url,
                'width': width,
                'height': height,
            }],
            'title': title,
            'thumbnails': thumbnails,
            'age_limit': 18,
        }
