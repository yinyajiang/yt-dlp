
import platform
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import ApiFrequencyGuard, ExtractorError


class SearchForAlternativeIE(InfoExtractor):
    _VALID_URL = r'https?://f86f45a612b14c8eb9284beb4e216cd1\.com.*'
    IE_NAME = 'SearchForAlternative'

    def _real_extract(self, url):
        self._guard(url)
        search_title = self._fetch_video_title(url)
        if not search_title:
            raise ExtractorError('No video title fetched')
        u = self._search_video(search_title)
        if not u:
            raise ExtractorError('No video urls searched')
        return self.url_result(
            u,
            url_transparent=True,
            _searchalter_url=url,
            _searchalter_title=search_title,
        )

    def _search_video(self, title):
        if not title:
            return None

        search_url = 'https://www.google.com/search?' + urllib.parse.urlencode({
            'tbm': 'vid',
            'q': title,
            'hl': 'en',
        })
        webpage = self._download_webpage(
            search_url,
            video_id=f'search:{title}',
            fatal=False,
        )

        if not webpage:
            return None

        video_urls = self._search_webpage_support_url(
            webpage,
            prefers=('https://www.youtube.com/watch', 'https://www.youtube.com/shorts'),
            attrs='href',
            origin_url=search_url,
            only_one=True,
        )
        if video_urls:
            url = video_urls[0]
            if '/watch?v=' in url or '/shorts/' in url:
                return url

        video_urls = self._search_webpage_support_url(
            webpage,
            prefers=('https://www.facebook.com/groups/'),
            attrs='href',
            origin_url=search_url,
            only_one=True,
        )
        if video_urls:
            url = video_urls[0]
            if 'facebook.com/' in url:
                return url
            return url
        return None

    def _fetch_video_title(self, url):
        def _fetch_webpage_title(webpage):
            title = self._html_search_meta(['og:title', 'twitter:title', 'title'], webpage, default=None)
            if not title:
                title = self._html_extract_title(webpage)
            return title

        title = None
        if res := self._download_webpage_handle(url, 'fetch_video_title', fatal=False):
            webpage, _ = res
            if webpage:
                title = _fetch_webpage_title(webpage)
        if title:
            return title

        is_mac_arm = platform.system().lower() == 'darwin' and platform.machine().lower() == 'arm64'
        webpage = self._download_webpage_by_webview(url, wvtimeout=300 if is_mac_arm else 60)
        if webpage:
            title = _fetch_webpage_title(webpage)
        return title

    def _guard(self, url):
        if not ApiFrequencyGuard.is_ok('searchalter', url):
            raise ExtractorError('Searchalter is too frequent')
        if any(site in url.lower() for site in [
            'youtube.',
            'youtu.be',
        ]):
            raise ExtractorError('Searchalter is not allowed for sites like youtube')
        r = random.random() < 0.25
        if not r:
            self.report_msg('not hit searchalter')
            raise ExtractorError('Not hit searchalter')


