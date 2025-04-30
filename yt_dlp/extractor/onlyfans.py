import json
import os
import urllib
import urllib.parse
import xml

from .common import InfoExtractor
from ..compat import compat_etree_fromstring
from ..utils import ExtractorError, determine_ext, to_bool


class OnlyfansIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onlyfans\.com.*'
    _TESTS = []
    IE_NAME = 'onlyfans'
    _nondrmsecrets = None

    def _get_external_ie_addr(self):
        addr = self._ie_args('external_ie')[0]
        if not addr:
            addr = os.getenv('onlyfans_external_ie')
            if not addr:
                raise ExtractorError('external_ie not found')
        try:
            port = int(addr)
            if port == 0:
                raise ExtractorError('external_ie port is 0')
            return f'http://127.0.0.1:{port}'
        except Exception:
            return addr

    def _call_external_ie(self, endpoint, note='Request External IE', large_timeout=False, **kwargs):
        addr = self._get_external_ie_addr()
        if not addr.endswith('/'):
            addr += '/'
        if 'data' in kwargs:
            if isinstance(kwargs['data'], dict):
                kwargs['data'] = json.dumps(kwargs['data']).encode()
            elif isinstance(kwargs['data'], str):
                kwargs['data'] = kwargs['data'].encode()

        if large_timeout:
            jsdata = self._no_proxy_download_large_timeout(addr + endpoint, note=note, **kwargs)
        else:
            jsdata = self._no_proxy_download_json(addr + endpoint, note=note, **kwargs)

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
            jsdata = self._call_external_ie('of/extract', data={
                'URL': url,
                'DisableCache': bool(self._ie_args('disable_cache')[0]),
                'MediaFilter': self._ie_args('media_filter'),
                'CountLimit': self._get_count_limit(),
            }, video_id=url, note='Extract media info using external ie', large_timeout=True)
            if jsdata['ExtractResult']['IsFromCache']:
                self.to_screen('Media info is from cache')
            medias = jsdata['ExtractResult']['Medias']
            proxy = jsdata['Proxy']

        if len(medias) == 1:
            info_dict = self._extract_media_info(url=url,
                                                 media=medias[0],
                                                 proxy=proxy,
                                                 load_formats=True,
                                                 panic=False)
            if info_dict:
                return info_dict

        has_drm = any(bool(media['IsDrm']) for media in medias)
        entries = []
        for i, media in enumerate(medias):
            entry = self._extract_media_info(url=self._url_add_params(url, 'index', str(i)),
                                             media=media,
                                             proxy=proxy,
                                             load_formats=(not has_drm) and (not self._downloader.params.get('extract_flat', False)),
                                             panic=(i == len(medias) - 1 and len(entries) == 0))
            if not entry:
                continue
            entries.append(entry)
        return self.playlist_result(entries, playlist_id=self._generic_id(url), playlist_title=jsdata['ExtractResult']['Title'])

    def _extract_media_info(self, url, media, proxy, load_formats=False, panic=True):
        try:
            media['Type'] = media['Type'].lower()
            if media['Type'] == 'gif' or media['Type'] == 'image' or media['Type'] == 'img':
                media['Type'] = 'photo'

            info_dict = {
                'id': str(media['PostID']) + '_' + str(media['MediaID']),
                'title': media['Title'],
                'ie_key': OnlyfansIE.IE_NAME,
            }
            if not proxy:
                self._info_dict_add_params(info_dict, 'proxy', '__noproxy__')
                # disable proxy
                self._set_disable_proxy()
            else:
                self._info_dict_add_params(info_dict, 'proxy', proxy)

            if load_formats:
                if to_bool(media['IsDrm']):
                    disable_cache = self._ie_args('disable_cache')[0]
                    try:
                        info_dict['formats'], secrets, headers = self._load_drm_formats(media['MediaURI'],
                                                                                        tip=url,
                                                                                        disable_cache=disable_cache)
                    except Exception as e:
                        if disable_cache or 'sign in' in str(e).lower():
                            raise
                        info_dict['formats'], secrets, headers = self._load_drm_formats(media['MediaURI'],
                                                                                        tip=media['MediaID'],
                                                                                        disable_cache=True)
                    info_dict['_drm_decrypt_key'] = secrets['DecryptKey']
                    self._info_dict_add_params(info_dict, 'http_headers', headers)
                else:
                    if self._nondrmsecrets is None:
                        self._nondrmsecrets = self._call_external_ie('of/nondrmsecrets', video_id=media['MediaID'], note='get nondrm secrets')
                    headers = self._nondrmsecrets['Headers']
                    info_dict['formats'] = [{
                        'format_id': 'none-drm',
                        'url': media['MediaURI'],
                        'ext': determine_ext(media['MediaURI'], default_ext=None),
                        'vcodec': 'none' if media['Type'] == 'audio' else None,
                        'http_headers': headers,
                    }]
                    info_dict['direct'] = True
                    info_dict['url'] = url
                    info_dict['webpage_url'] = url
                    self._info_dict_add_params(info_dict, 'http_headers', headers)
            else:
                info_dict['url'] = self._encode_media_to_url(media, proxy)
                info_dict['_type'] = 'url'
            return info_dict
        except Exception:
            if panic:
                raise
            return None

    def _load_drm_formats(self, media_uri, tip, disable_cache):
        if not tip:
            tip = 'drm video'
        secrets = self._call_external_ie('of/drmsecrets', data={
            'MediaURI': media_uri,
            'DisableCache': disable_cache,
        }, video_id=tip, note='Extract drm secrets using external ie')
        headers = secrets['Headers']
        headers['Cookie'] = secrets['CookiesString']
        request_webpage = self._request_webpage(secrets['MPDURL'], video_id=tip, headers=headers)
        webpage = self._webpage_read_content(request_webpage, secrets['MPDURL'], video_id=tip)
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

    def _url_add_params(self, url, k, v):
        if '?' in url:
            return f'{url}&{k}={v}'
        return f'{url}?{k}={v}'

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
        media['IsDrm'] = to_bool(query_params.get('IsDrm', [None])[0])
        return media, query_params.get('proxy', [None])[0]

    def _set_disable_proxy(self):
        self._downloader.params['proxy'] = ''

    def _get_count_limit(self):
        try:
            items = str(self._downloader.params.get('playlist_items', '')).split('-')
            if len(items) == 2:
                return int(items[1]) - int(items[0]) + 1
            if len(items) == 1:
                return int(items[0])
        except Exception:
            pass
        return -1
