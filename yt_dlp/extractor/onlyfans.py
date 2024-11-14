import json
import urllib
import urllib.parse
import xml

from .common import InfoExtractor
from ..compat import compat_etree_fromstring
from ..utils import ExtractorError, determine_ext


class OnlyfansIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onlyfans\.com.*'
    _TESTS = []
    IE_NAME = 'onlyfans'
    _nondrmsecrets = None

    def _call_external_ie(self, endpoint, note='Request External IE', large_timeout=False, **kwargs):
        addr = self._ie_args('external_ie')[0]
        if not addr:
            raise ExtractorError('external_ie not found')
        if not addr.endswith('/'):
            addr += '/'
        if 'data' in kwargs:
            if isinstance(kwargs['data'], dict):
                kwargs['data'] = json.dumps(kwargs['data']).encode()
            elif isinstance(kwargs['data'], str):
                kwargs['data'] = kwargs['data'].encode()
        try:
            if large_timeout:
                old_timeout = self._downloader.params.get('socket_timeout', None)
                self._downloader.params['socket_timeout'] = 9999
            jsdata = self._download_json(addr + endpoint, note=note, **kwargs)
        finally:
            if large_timeout:
                if old_timeout is None:
                    self._downloader.params.pop('socket_timeout', None)
                else:
                    self._downloader.params['socket_timeout'] = old_timeout
        if not jsdata:
            raise ExtractorError('No data returned from external IE')
        if 'error' in jsdata:
            raise ExtractorError(jsdata['error'])
        return jsdata

    def _real_extract(self, url):
        if self._is_url_with_media(url):
            self.to_screen('Decoding encoded media url')
            media, proxy = self._decode_url_with_media(url)
            medias = [media]
        else:
            jsdata = self._call_external_ie('extract', data={
                'URL': url,
                'DisableCache': bool(self._ie_args('disable_cache')[0]),
                'MediaFilter': self._ie_args('media_filter'),
            }, video_id=url, note='Extract media info using external ie', large_timeout=True)
            if jsdata['ExtractResult']['IsFromCache']:
                self.to_screen('Media info is from cache')
            medias = jsdata['ExtractResult']['Medias']
            proxy = jsdata['Proxy']

        if len(medias) == 1:
            return self._extract_media_info(tip_video_id=url,
                                            media=medias[0],
                                            proxy=proxy,
                                            load_drm_formats=True,
                                            panic=True)

        entries = []
        for i, media in enumerate(medias):
            load_formats = not media['IsDrm'] or not self.get_param('extract_flat', False)
            entry = self._extract_media_info(tip_video_id=media['MediaID'],
                                             media=media,
                                             proxy=proxy,
                                             load_drm_formats=load_formats,
                                             panic=(i == len(medias) - 1 and len(entries) == 0))
            if not entry:
                continue
            entries.append(entry)
        return self.playlist_result(entries, playlist_title=jsdata['ExtractResult']['Title'])

    def _extract_media_info(self, tip_video_id, media, proxy, load_drm_formats=False, panic=True):
        try:
            media['Type'] = media['Type'].lower()
            if media['Type'] == 'gif' or media['Type'] == 'image' or media['Type'] == 'img':
                media['Type'] = 'photo'

            info_dict = {
                'id': str(media['PostID']) + '_' + str(media['MediaID']),
                'title': media['Title'],
            }
            if not proxy:
                self._info_dict_add_params(info_dict, 'proxy', '__noproxy__')
                # disable proxy
                self._downloader.params['proxy'] = ''
            else:
                self._info_dict_add_params(info_dict, 'proxy', proxy)

            if media['IsDrm']:
                if load_drm_formats:
                    disable_cache = self._ie_args('disable_cache')[0]
                    try:
                        info_dict['formats'], secrets, headers = self._load_drm_formats(media['MediaURI'],
                                                                                        tip_video_id=tip_video_id,
                                                                                        disable_cache=disable_cache)
                    except Exception as e:
                        if disable_cache or 'sign in' in str(e).lower():
                            raise
                        info_dict['formats'], secrets, headers = self._load_drm_formats(media['MediaURI'],
                                                                                        tip_video_id=tip_video_id,
                                                                                        disable_cache=True)
                    info_dict['_drm_decrypt_key'] = secrets['DecryptKey']
                    self._info_dict_add_params(info_dict, 'http_headers', headers)
                else:
                    info_dict['url'] = self._encode_media_to_url(media, proxy)
                    info_dict['_type'] = 'url'
                return info_dict
            else:
                if self._nondrmsecrets is None:
                    self._nondrmsecrets = self._call_external_ie('nondrmsecrets', video_id=tip_video_id, note='get nondrm secrets')
                headers = self._nondrmsecrets['Headers']
                info_dict['formats'] = [{
                    'format_id': 'none-drm',
                    'url': media['MediaURI'],
                    'ext': determine_ext(media['MediaURI'], default_ext=None),
                    'vcodec': 'none' if media['Type'] == 'audio' else None,
                    'http_headers': headers,
                }]
                info_dict['direct'] = True
                self._info_dict_add_params(info_dict, 'http_headers', headers)
                return info_dict
        except Exception:
            if panic:
                raise
            return None

    def _load_drm_formats(self, media_uri, tip_video_id, disable_cache):
        if not tip_video_id:
            tip_video_id = 'drm video'
        secrets = self._call_external_ie('drmsecrets', data={
            'MediaURI': media_uri,
            'DisableCache': disable_cache,
        }, video_id=tip_video_id, note='Extract drm secrets using external ie')
        headers = secrets['Headers']
        headers['Cookie'] = secrets['CookiesString']
        request_webpage = self._request_webpage(secrets['MPDURL'], video_id=tip_video_id, headers=headers)
        webpage = self._webpage_read_content(request_webpage, secrets['MPDURL'], video_id=tip_video_id)
        try:
            doc = compat_etree_fromstring(webpage)
        except xml.etree.ElementTree.ParseError:
            doc = compat_etree_fromstring(webpage.encode())
        formats = self._parse_mpd_formats(
            doc,
            mpd_base_url=request_webpage.url.rpartition('/')[0],
            mpd_url=secrets['MPDURL'])
        for fmt in formats:
            fmt['http_headers'] = headers
            fmt['cookies'] = headers['Cookie']
            if 'has_drm' in fmt:
                del fmt['has_drm']
            if '_has_drm' in fmt:
                del fmt['_has_drm']
        return formats, secrets, headers

    def _ie_args(self, name):
        args = self._configuration_arg(name, [], ie_key=OnlyfansIE, casesense=True)
        if not args:
            return [None]
        if not isinstance(args, list):
            return [args]
        return args

    def _info_dict_add_params(self, info_dict, k, v):
        if '_params' not in info_dict:
            info_dict['_params'] = {}
        info_dict['_params'][k] = v

    def _encode_media_to_url(self, media, proxy):
        params = urllib.parse.urlencode({
            'MediaURI': media['MediaURI'],
            'Type': media['Type'],
            'PostID': media['PostID'],
            'MediaID': media['MediaID'],
            'Title': media['Title'],
            'IsDrm': media['IsDrm'],
            'proxy': proxy,
        })
        return f'https://onlyfans.com?__media_info_=true&{params}'

    def _is_url_with_media(self, url):
        return '__media_info_=true' in url

    def _decode_url_with_media(self, url):
        if not self._is_url_with_media(url):
            raise ExtractorError('Not an encoded media url')
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        media = {}
        media['MediaURI'] = query_params.get('MediaURI', [None])[0]
        media['Type'] = query_params.get('Type', [None])[0]
        media['PostID'] = query_params.get('PostID', [None])[0]
        media['MediaID'] = query_params.get('MediaID', [None])[0]
        media['Title'] = query_params.get('Title', [None])[0]
        media['IsDrm'] = query_params.get('IsDrm', [None])[0]
        return media, query_params.get('proxy', [None])[0]
