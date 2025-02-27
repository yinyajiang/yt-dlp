import itertools
import re

from .common import ExtractorError, InfoExtractor, SearchInfoExtractor


class GoogleSearchIE(SearchInfoExtractor):
    IE_DESC = 'Google Video search'
    IE_NAME = 'video.google:search'
    _SEARCH_KEY = 'gvsearch'
    _TESTS = [{
        'url': 'gvsearch15:python language',
        'info_dict': {
            'id': 'python language',
            'title': 'python language',
        },
        'playlist_count': 15,
    }]
    _PAGE_SIZE = 100

    def _search_results(self, query):
        for pagenum in itertools.count():
            webpage = self._download_webpage(
                'http://www.google.com/search', f'gvsearch:{query}',
                note=f'Downloading result page {pagenum + 1}',
                query={
                    'tbm': 'vid',
                    'q': query,
                    'start': pagenum * self._PAGE_SIZE,
                    'num': self._PAGE_SIZE,
                    'hl': 'en',
                })

            for url in re.findall(r'<div[^>]* class="dXiKIc"[^>]*><a href="([^"]+)"', webpage):
                yield self.url_result(url)

            if not re.search(r'id="pnnext"', webpage):
                return


class GoogleSearchPageIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?google\.[a-zA-Z0-9\-]+/search/?.*'
    _TESTS = [
        {
            'url': 'https://www.google.com/search?sca_esv=6ad49f876c4c6d05&sxsrf=AHTn8zoMjhgBxqv6FCDGwddC8COhuK-qqA:1740634483185&q=sag&udm=7&fbs=ABzOT_CWdhQLP1FcmU5B0fn3xuWpmDtIGL1r84kuKz6yAcD_igefx-eKq1gCPHF3zhthFomUWD4JA37sWEIpiDUfp9if64PTOXxbEepEjc-nDfPpzIEeHPiuNSdNZGuuRQlrLDjlRtxGxtiuxpaGEJ92kmgo0df5dLBhdVCUQf9beyUBCj7tbBto6oXPqq_GDmfgi6xxY3sdZD8M_GL_WrxUB3p48Ff6Xw&sa=X&ved=2ahUKEwiihLfgkOOLAxULle4BHfXWKigQtKgLegQIGRAB&biw=2482&bih=1294&dpr=1',
            'only_matching': True,
        },
        {
            'url': 'https://www.google.com/search?q=create%20settings%20on%20computer%20podgo&source=sh/x/gs/m2/5#fpstate=ive&vld=cid:93f2cb2b,vid:QpL8yTYJ-o4,st:0',
            'only_matching': True,
        },
        {
            'url': 'https://www.google.com/search?sca_esv=8a5f3c529fc99551&rlz=1C1GEWG_enZA990ZA990&sxsrf=AHTn8zpiqTzDl9IYUQhz87ApLrNBwXOHiQ:1740081463098&q=facts+about+the+leopards&udm=7&fbs=ABzOT_CWdhQLP1FcmU5B0fn3xuWpA-dk4wpBWOGsoR7DG5zJBjLjqIC1CYKD9D-DQAQS3Z6fZ--OaZn3DMTxQWxLIg4hDloclsc7MfX2RhZx9tXQHZQhmbP1894chDgnwLczlW513IKYDs8bQd9LqNHCm4tcnj3yCiy_FNSavQu2ARBpZCCY6JIxmRfh6QIdQRUJz0KmxTTezOI5_gxUTX_6b9hHeOVUjg&sa=X&ved=2ahUKEwjgzfPLhNOLAxUiXEEAHflAEwEQtKgLegQIKRAB&biw=1360&bih=641&dpr=1#fpstate=ive&vld=cid:d225cb1d,vid:luZqsECnmUI,st:0',
            'only_matching': True,
        },
        {
            'url': 'https://www.google.pl/search?q=jak+sprawdzi%C4%87+klucz+windows+10&sca_esv=e43f164304cbaefd&source=hp&ei=kCShZ9eDAeWMxc8P4P71-Ac&iflsig=ACkRmUkAAAAAZ6EyoP3Kjhz2-mexR0q16IDPgOFCaZot&oq=Jak+sprawdzi%C4%87+klucz&gs_lp=Egdnd3Mtd2l6IhRKYWsgc3ByYXdkemnEhyBrbHVjeioCCAEyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAESPWQAVCID1iAe3ABeACQAQCYAWmgAZwKqgEEMTguMbgBAcgBAPgBAZgCFKAC9guoAgrCAgoQABgDGOoCGI8BwgIKEC4YAxjqAhiPAcICDhAuGIAEGLEDGNEDGMcBwgIOEAAYgAQYsQMYgwEYigXCAggQLhiABBjUAsICBRAuGIAEwgILEAAYgAQYsQMYgwHCAggQABiABBixA8ICDhAuGIAEGLEDGIMBGIoFwgILEC4YgAQYsQMYgwHCAggQLhiABBixA8ICCxAuGIAEGMcBGK8BwgILEAAYgAQYsQMYyQPCAgsQLhiABBixAxjUAsICCBAAGIAEGJIDwgILEAAYgAQYkgMYigXCAgcQABiABBgKwgIOEAAYgAQYsQMYgwEYyQPCAgsQABiABBixAxiKBZgDCvEFGoTInrhU8gGSBwQxOS4xoAfgkgE&sclient=gws-wiz#fpstate=ive&vld=cid:fec8f0ac,vid:utI7tYuzhWk,st:0',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        vid_match = re.search(r'#.*?vid:(?P<vid>[^&#,]+)', url)
        if vid_match and vid_match.group('vid'):
            return self.url_result(f'https://www.youtube.com/watch?v={vid_match.group("vid")}')

        result = self._fetch_url_reslut(url, 'google search')
        if result:
            return result
        raise ExtractorError('No video URL found')

    def _fetch_url_reslut(self, url, hint):
        webpage = self._download_webpage(url, hint)
        # search support url
        srcs = self._search_webpage_support_url(webpage, prefers=('https://www.youtube.com', ), attrs='href', origin_url=url)
        if srcs:
            return self.url_result(srcs[0])
        return None
