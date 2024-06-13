import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_duration,
    remove_end,
    unified_strdate,
)


class Porn91IE(InfoExtractor):
    IE_NAME = '91porn'
    _VALID_URL = r'(?:https?://)(?:www\.|)91porn\.com/view_video.php\?([^#]+&)?viewkey=(?P<id>\w+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._set_cookie('91porn.com', 'language', 'cn_CN')

        webpage = self._download_webpage(
            f'http://91porn.com/view_video.php?viewkey={video_id}', video_id)

        if '视频不存在,可能已经被删除或者被举报为不良内容!' in webpage:
            raise ExtractorError('91 Porn says: Video does not exist', expected=True)

        daily_limit = self._search_regex(
            r'作为游客，你每天只可观看([\d]+)个视频', webpage, 'exceeded daily limit', default=None, fatal=False)
        if daily_limit:
            raise ExtractorError(f'91 Porn says: Daily limit {daily_limit} videos exceeded', expected=True)

        video_link_url = self._search_regex(
            r'document\.write\(\s*strencode2\s*\(\s*((?:"[^"]+")|(?:\'[^\']+\'))', webpage, 'video link')
        video_link_url = self._search_regex(
            r'src=["\']([^"\']+)["\']', urllib.parse.unquote(video_link_url), 'unquoted video link')

        formats, subtitles = self._get_formats_and_subtitle(video_link_url, video_id)

        return {
            'id': video_id,
            'title': remove_end(self._html_extract_title(webpage).replace('\n', ''), 'Chinese homemade video').strip(),
            'formats': formats,
            'subtitles': subtitles,
            'upload_date': unified_strdate(self._search_regex(
                r'<span\s+class=["\']title-yakov["\']>(\d{4}-\d{2}-\d{2})</span>', webpage, 'upload_date', fatal=False)),
            'description': self._html_search_regex(
                r'<span\s+class=["\']more title["\']>\s*([^<]+)', webpage, 'description', fatal=False),
            'duration': parse_duration(self._search_regex(
                r'时长:\s*<span[^>]*>\s*(\d+(?::\d+){1,2})', webpage, 'duration', fatal=False)),
            'comment_count': int_or_none(self._search_regex(
                r'留言:\s*<span[^>]*>\s*(\d+)\s*</span>', webpage, 'comment count', fatal=False)),
            'view_count': int_or_none(self._search_regex(
                r'热度:\s*<span[^>]*>\s*(\d+)\s*</span>', webpage, 'view count', fatal=False)),
            'age_limit': 18,
        }

    def _get_formats_and_subtitle(self, video_link_url, video_id):
        ext = determine_ext(video_link_url)
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(video_link_url, video_id, ext='mp4')
        else:
            formats = [{'url': video_link_url, 'ext': ext}]
            subtitles = {}

        return formats, subtitles
