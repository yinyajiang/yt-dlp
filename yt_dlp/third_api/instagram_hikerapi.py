import urllib.parse
from ..utils import traverse_obj, ExtractorError
from ..cookies import YoutubeDLCookieJar
import json
import os


class InstagramHikerApi:
    API_HOST = 'https://api.hikerapi.com'

    def __init__(self, ie):
        self._ie = ie
        self._api_keys = ie._configuration_arg('hikerapi_key', [], casesense=True, ie_key='Instagram')
        if not self._api_keys and os.getenv('hikerapi_key'):
            self._api_keys = [os.getenv('hikerapi_key')]
        if not ie:
            raise ExtractorError('[hikerapi] ie is required')
        if not self._api_keys:
            raise ExtractorError('[hikerapi] api keys is required')

        self._prefer_video = True
        if not_prefer_video := ie._configuration_arg('hikerapi_not_prefer_video', [], casesense=True, ie_key='Instagram', enable_env=True):
            self._prefer_video = not not_prefer_video[0]

        self._default_max_call_page = 50
        if max_call_page := ie._configuration_arg('hikerapi_max_call_page', [], casesense=True, ie_key='Instagram', enable_env=True):
            self._default_max_call_page = max_call_page[0]

    def extract_user_stories_info(self, username='', user_id=''):
        """Extract user stories by username or user_id"""
        if not username and not user_id:
            raise ExtractorError('[hikerapi] username or user_id is required')

        if username:
            js = self._call_api('/v2/user/stories/by/username', {'username': username})
        else:
            js = self._call_api('/v2/user/stories', {'user_id': user_id})

        reel = traverse_obj(js, 'reel', default={})
        user = traverse_obj(reel, 'user', default={})
        if not user and not reel:
            raise ExtractorError('[hikerapi]: ' + json.dumps(js))

        info = {
            'id': str(user.get('pk_id')),
            '_type': 'playlist',
            'title': f'{user.get("username")} Story',
            'url': f'https://www.instagram.com/stories/{user.get("username")}',
            'description': user.get('full_name'),
            'thumbnails': [{'url': user.get('profile_pic_url')}],
            'entries': [],
        }

        for item in traverse_obj(reel, ('items', ...), default=[]):
            info['entries'].append(self._parse_media_info(item))

        info['entries'] = self._filter_entries(info['entries'])
        return info

    def extract_user_highlights_info(self, username='', user_id=''):
        """Extract user highlights by username or user_id"""
        if not username and not user_id:
            raise ExtractorError('[hikerapi] username or user_id is required')
        if username:
            js = self._call_api('/v2/user/highlights/by/username', {'username': username})
        else:
            js = self._call_api('/v2/user/highlights', {'user_id': user_id})

        reel = traverse_obj(js, 'reel', default={})
        user = traverse_obj(reel, 'user', default={})
        if not user and not reel:
            raise ExtractorError('[hikerapi]: ' + json.dumps(js))

        info = {
            'id': str(user.get('pk_id')),
            '_type': 'playlist',
            'title': f'{user.get("username")} Story',
            'url': f'https://www.instagram.com/stories/{user.get("username")}',
            'description': user.get('full_name'),
            'thumbnails': [{'url': user.get('profile_pic_url')}],
            'entries': [],
        }

        for item in traverse_obj(reel, ('items', ...), default=[]):
            info['entries'].append(self._parse_media_info(item))

        info['entries'] = self._filter_entries(info['entries'])
        return info

    def extract_user_posts_info(self, user_id='', username='', max_call_page=None):
        """Extract user posts with pagination support"""
        if not user_id and not username:
            raise ExtractorError('[hikerapi] user_id or username is required')

        if not max_call_page:
            max_call_page = self._default_max_call_page

        if max_call_page <= 0:
            max_call_page = -1
        if not user_id:
            user = self._get_user_info(username=username)
            user_id = user.get('id')
        else:
            user = {
                'id': str(user_id),
                'title': 'post by ' + username or user_id,
            }

        entries = []
        page = {'end': False, 'next_page_id': ''}

        while not page['end'] and max_call_page != 0:
            entries = self._extract_user_posts_with_pagination(user_id, page)
            if not entries:
                break
            entries.extend(entries)
            max_call_page -= 1

        return {
            **user,
            '_type': 'playlist',
            'entries': self._filter_entries(entries),
        }

    def extract_post_info(self, code='', id=''):
        """Extract post information by code or id"""
        if not code and not id:
            raise ExtractorError('[hikerapi] code or id is required')
        if code:
            js = self._call_api('/v2/media/info/by/code', {'code': code})
        else:
            js = self._call_api('/v2/media/info/by/id', {'id': id})
        if js.get('status', '').lower() != 'ok':
            raise ExtractorError('[hikerapi] ' + json.dumps(js))

        return self._parse_media_info(js.get('media_or_ad'))

    def extract_story_info(self, story_id=''):
        js = self._call_api('/v2/story/by/id', {'id': story_id})
        if js.get('status', '').lower() != 'ok':
            raise ExtractorError('[hikerapi] ' + json.dumps(js))

        reel = traverse_obj(js, 'reel', default={})
        user = traverse_obj(reel, 'user', default={})

        info = {
            'id': str(user.get('pk_id')),
            '_type': 'playlist',
            'title': f'{user.get("username")} Story',
            'url': f'https://www.instagram.com/stories/{story_id}',
            'description': user.get('full_name'),
            'thumbnails': [{'url': user.get('profile_pic_url')}],
            'entries': [],
        }

        for item in traverse_obj(reel, ('items', ...), default=[]):
            info['entries'].append(self._parse_media_info(item))

        info['entries'] = self._filter_entries(info['entries'])

    def _filter_entries(self, entries):
        if self._prefer_video:
            filter_entries = [entry for entry in entries if entry.get('_media_type') == 'VIDEO']
            if filter_entries:
                entries = filter_entries
        return entries

    def _extract_user_posts_with_pagination(self, user_id, page):
        if page['end']:
            return []

        js = self._call_api('/v2/user/medias/', {
            'user_id': user_id,
            'page_id': page['next_page_id'],
        })

        num = traverse_obj(js, ('response', 'num_results'), default=0)
        if num <= 0:
            page['end'] = True
            return []

        entries = []
        for item in traverse_obj(js, ('response', 'items', ...), default=[]):
            entries.append(self._parse_media_info(item))

        page['end'] = not traverse_obj(js, ('response', 'more_available'), default=False)
        page['next_page_id'] = traverse_obj(js, ('response', 'next_page_id'), default='')
        if not page['next_page_id']:
            page['end'] = True

        return entries

    def _parse_media_info(self, item):
        """Parse media information from API response"""
        user_name = traverse_obj(item, ('user', 'username'), default='')
        media_id = traverse_obj(item, 'pk', default='')
        code = traverse_obj(item, 'code', default='')
        thumbnail = traverse_obj(item, 'thumbnail_url', default='') or traverse_obj(
            item, ('image_versions2', 'candidates', 0, 'url'), default='')
        title = traverse_obj(item, ('caption', 'text'), default='') or f'Post by {user_name}'

        entry = {
            'id': str(media_id),
            'title': title,
            'thumbnails': [{'url': thumbnail}] if thumbnail else None,
            # 'upload_date': datetime.fromtimestamp(
            #     traverse_obj(item, 'taken_at', default=0)),
        }

        if code:
            entry['webpage_url'] = f'https://www.instagram.com/p/{code}'
        elif traverse_obj(item, 'product_type') == 'story':
            entry['webpage_url'] = f'https://www.instagram.com/stories/{user_name}/{media_id}'

        format_urls = set()

        media_type = traverse_obj(item, 'media_type', default=0)
        if media_type == 1:  # Photo
            if entry.get('formats') is None:
                entry['formats'] = []
            entry['_media_type'] = 'PHOTO'
            for img in traverse_obj(item, ('image_versions2', 'candidates', ...), default=[]):
                if img.get('url') in format_urls:
                    continue
                format_urls.add(img.get('url'))
                entry['formats'].append({
                    'url': img.get('url'),
                    'width': img.get('width'),
                    'height': img.get('height'),
                })

        elif media_type == 2:  # Video
            if entry.get('formats') is None:
                entry['formats'] = []
            entry['_media_type'] = 'VIDEO'
            entry['duration'] = traverse_obj(item, 'video_duration', default=0)
            for vid in traverse_obj(item, ('video_versions', ...), default=[]):
                if vid.get('url') in format_urls:
                    continue
                format_urls.add(vid.get('url'))
                entry['formats'].append({
                    'url': vid.get('url'),
                    'width': vid.get('width'),
                    'height': vid.get('height'),
                })

        elif media_type == 8:  # Carousel
            entry['_playlist_media_type'] = 'CAROUSEL'
            entry['_type'] = 'playlist'
            if entry.get('entries') is None:
                entry['entries'] = []
            for sub_item in traverse_obj(item, ('carousel_media', ...), default=[]):
                sub_entry = self._parse_media_info(sub_item)
                if not sub_entry.get('webpage_url'):
                    sub_entry['webpage_url'] = entry['webpage_url']
                if sub_entry.get('entries'):
                    entry['entries'].extend(sub_entry['entries'])
                else:
                    entry['entries'].append(sub_entry)

        return entry

    def _get_user_info(self, username='', user_id=''):
        """Extract user information by username or user_id"""
        if username:
            js = self._call_api('/v2/user/by/username/', {'username': username})
        else:
            js = self._call_api('/v2/user/by/id/', {'id': user_id})

        user = traverse_obj(js, 'user', default={})
        info = {
            'id': str(user.get('pk_id')),
            'title': user.get('username'),
            'url': f'https://www.instagram.com/{user.get("username")}',
            'description': user.get('biography'),
            'thumbnail': user.get('profile_pic_url'),
            'media_count': user.get('media_count'),
            '_is_private': user.get('is_private'),
        }
        if info.get('_is_private'):
            self._ie.report_msg(f'[hikerapi] user {username or user_id} is private')
        return info

    def _call_api(self, api: str, params=None, tip=None) -> dict:
        """Make API call to HikerAPI"""
        def download_json(url, **kwargs):
            return self._ie._download_json(url, tip if tip else 'call hikerapi', **kwargs)

        def report_msg(msg):
            self._ie.report_msg(f'[hikerapi] {msg}')

        query = ('?' + urllib.parse.urlencode(params)) if params else ''
        url = f'{self.API_HOST}/{api.strip("/")}{query}'
        return download_json(url, headers={
            'x-access-key': self._api_keys[0],
            'accept': 'application/json',
        },
            extensions={
                'cookiejar': YoutubeDLCookieJar(),
        },
            expected_status=lambda _: True,
        )
