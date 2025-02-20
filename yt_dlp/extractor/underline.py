from .common import InfoExtractor


def gen_dict_extract(var, key):
    if hasattr(var, 'items'):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(v, key):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(d, key):
                        yield result


class UnderlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?underline\.io/events/(?P<id>[^?]+).*'

    _TESTS = [
        {
            'url': 'https://underline.io/events/342/posters/12863/poster/66463-mbti-personality-prediction-approach-on-persian-twitter?tab=video',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        webpage_info = self._search_json(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">',
            webpage,
            'idk_what_this_arg_does',
            video_id,
            end_pattern=r'</script>',
        )

        title = list(gen_dict_extract(webpage_info, 'title'))

        if len(title) == 0:
            title = None
        else:
            title = title[0]

        playlist_urls = list(gen_dict_extract(webpage_info, 'playlist'))

        if len(playlist_urls) == 0:
            url = None
        else:
            url = playlist_urls[0]

        formats = []

        m3u8_url = url
        if m3u8_url:
            formats.extend(
                self._extract_m3u8_formats(
                    m3u8_url,
                    video_id,
                    ext='mp4',
                    entry_protocol='m3u8_native',
                ),
            )

        # slide_info = list(gen_dict_extract(webpage_info, "slideshow"))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            # "slide_info": slide_info,
        }
