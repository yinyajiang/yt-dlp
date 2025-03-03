import re
import urllib.parse

from .common import ExtractorError, InfoExtractor
from ..utils import api_base_url


class BingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[a-zA-Z]+\.)?bing\.(?P<loc>[a-zA-Z0-9\-]+)/.*'

    _TESTS = [{
        'url': 'https://www.bing.com/ck/a?!&&p=e35b31bb082116548575f8180c318ec77c43cb41560d9748eb02601ed3046311JmltdHM9MTczODE5NTIwMA&ptn=3&ver=2&hsh=4&fclid=109d2c87-26d0-6907-357f-3f73270268af&psq=Alwyn+Crawshaw+Watercolour+Tutorials&u=a1aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g_dj1kblY3eDhHVGlFcw&ntb=1',
        'only_matching': True,
    },
        {
        'url': 'https://www.bing.com/ck/a?!&&p=9acc263d8101e2f84216b6dadce4a0d98dce95830cbe8176669eb685f12b42e5JmltdHM9MTczOTE0NTYwMA&ptn=3&ver=2&hsh=4&fclid=0e65d243-74b2-611a-0dfd-c7c8752b60e5&u=a1L3NlYXJjaD9xPVN1cGVyK0Jvd2wreHh2aWlpK2Z1bGwrZ2FtZSZGT1JNPVI1RkQ&ntb=1',
        'only_matching': True,
    },
    ]

    def _real_extract(self, url):
        result = self._fetch_url_reslut(url, 'bing search')
        if result:
            return result
        loc = self._match_valid_url(url).group('loc')
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if query_params and query_params.get('q'):
            bind_videos_url = f'https://bing.{loc}/videos?q=' + urllib.parse.quote(query_params['q'][0])
            result = self._fetch_url_reslut(bind_videos_url, 'search bing videos')
            if result:
                return result
        raise ExtractorError('No video URL found')

    def _fetch_url_reslut(self, url, hint):
        webpage = self._download_webpage(url, hint)

        # position video url
        match = re.search(r'var\s+u\s*=\s*(["\'])(?P<url>https?:[^\1;]*?)\1', webpage)
        if match:
            video_url = match.group('url')
            return self.url_result(video_url)

        # download redirect webpage
        match = re.search(r'var\s+u\s*=\s*(["\'])(?P<url>/[^\1;]+?)\1', webpage)
        redirect_url = None
        if match:
            redirect_url = api_base_url(url) + match.group('url')
            webpage = self._download_webpage(redirect_url, 'bing redirect')

        # search support url
        srcs = self._search_webpage_support_url(webpage, prefers=('https://www.youtube.com', ), attrs='href', origin_url=redirect_url if redirect_url else url)
        if srcs:
            return self.url_result(srcs[0])
        return None
