import re

from .common import InfoExtractor
from ..utils import OnDemandPagedList, get_element_by_class, traverse_obj


class QingTingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?(?:qingting\.fm|qtfm\.cn)/v?channels/(?P<channel>\d+)/programs/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.qingting.fm/channels/378005/programs/22257411/',
        'md5': '47e6a94f4e621ed832c316fd1888fb3c',
        'info_dict': {
            'id': '22257411',
            'title': '用了十年才修改，谁在乎教科书？',
            'channel_id': '378005',
            'channel': '睡前消息',
            'uploader': '马督工',
            'ext': 'm4a',
        },
    }, {
        'url': 'https://m.qtfm.cn/vchannels/378005/programs/23023573/',
        'md5': '2703120b6abe63b5fa90b975a58f4c0e',
        'info_dict': {
            'id': '23023573',
            'title': '【睡前消息488】重庆山火之后，有图≠真相',
            'channel_id': '378005',
            'channel': '睡前消息',
            'uploader': '马督工',
            'ext': 'm4a',
        },
    }]

    def _real_extract(self, url):
        channel_id, pid = self._match_valid_url(url).group('channel', 'id')
        webpage = self._download_webpage(
            f'https://m.qtfm.cn/vchannels/{channel_id}/programs/{pid}/', pid)
        info = self._search_json(r'window\.__initStores\s*=', webpage, 'program info', pid)
        return {
            'id': pid,
            'title': traverse_obj(info, ('ProgramStore', 'programInfo', 'title')),
            'channel_id': channel_id,
            'channel': traverse_obj(info, ('ProgramStore', 'channelInfo', 'title')),
            'uploader': traverse_obj(info, ('ProgramStore', 'podcasterInfo', 'podcaster', 'nickname')),
            'url': traverse_obj(info, ('ProgramStore', 'programInfo', 'audioUrl')),
            'vcodec': 'none',
            'acodec': 'm4a',
            'ext': 'm4a',
        }


class QingTingChannelIE(InfoExtractor):
    IE_NAME = 'QingTing:Channel'
    IE_DESC = '蜻蜓FM 专辑'
    _VALID_URL = r'https?://(?:www\.|m\.)?(?:qingting\.fm|qtfm\.cn)/v?channels/(?P<id>\d+)(?:/(?P<pageIdx>\d+))?/?(?:\?[^/]*)?$'
    _TESTS = [{
        'url': 'https://www.qingting.fm/channels/324131',
        'info_dict': {
            'title': '小学篇',
            'id': '324131',
        },
        'playlist_mincount': 75,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        start_page_idx = self._match_valid_url(url).group('pageIdx')
        if not start_page_idx:
            start_page_idx = 1

        first_page = self._fetch_page(playlist_id, start_page_idx)

        playlist_title = self._html_extract_title(first_page).strip()
        if not playlist_title:
            playlist_title = playlist_id
        if playlist_title[0] != '-':
            playlist_title = playlist_title.split('-')[0].strip()

        entries = OnDemandPagedList(
            lambda idx: self._get_entries(playlist_title, playlist_id, self._fetch_page(playlist_id, idx + 1) if idx else first_page),
            30)

        return self.playlist_result(entries, playlist_id, playlist_title)

    def _fetch_page(self, playlist_id, page_idx):
        return self._download_webpage(
            f'https://www.qingting.fm/channels/{playlist_id}/{page_idx}',
            playlist_id,
            note='Download channel page for %s' % playlist_id,
            errnote='Unable to get channel info')

    def _get_entries(self, playlist_title, playlist_id, page_data):
        programList = get_element_by_class('programList', page_data)
        if not programList:
            return
        hrefMatchs = re.findall(r'href\s*=\s*(["\'])(.+?)\1', programList)
        if not hrefMatchs:
            return

        titleMatchs = re.findall(r'title\s*=\s*(["\'])(.+?)\1', programList)

        for i, hrefMatch in enumerate(hrefMatchs):
            if playlist_id not in hrefMatch[1]:
                continue
            program_url = f'https://www.qingting.fm{hrefMatch[1]}'
            program_id = hrefMatch[1].split('/')[-1]
            if len(titleMatchs) == len(hrefMatchs):
                program_title = titleMatchs[i][1].strip()
            if not program_title:
                program_title = f'{playlist_title} - {i}'
            yield self.url_result(program_url, QingTingIE, program_id, program_title)
