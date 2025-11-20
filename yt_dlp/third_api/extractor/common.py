import urllib.parse
from ...utils import remove_query_params, ExtractorError
from ...utils._utils import locked_file
import os
import tempfile
import json
import time


class RetryError(Exception):
    pass


class OverPerSecondError(Exception):
    pass


def is_retry_rsp(rsp):
    if not rsp:
        return False
    msg = str(rsp).lower()
    return 'please try again later' in msg


def is_over_per_second_rsp(rsp):
    if not rsp:
        return False
    msg = str(rsp).lower()
    return 'per second' in msg


def is_supported_site(hint, support_sites):
    try:
        url = urllib.parse.urlparse(hint)
        if url.netloc:
            hint = url.netloc
    except Exception:
        pass
    if not hint:
        return False
    hint = hint.lower()
    if hint.startswith('www.'):
        hint = hint[4:]
    hint = hint.split(':')[0]
    hints = hint.split('.')
    if len(hints) >= 2:
        hints = hints[0:2]
    for s in hints:
        if not s:
            continue
        if s in [site.lower() for site in support_sites]:
            return True
    return False


def remove_third_api_params(video_url):
    return remove_query_params(video_url, ['__force_third_api__', '__third_api__'])


class ThirdApiGuard:

    @staticmethod
    def guard(ie, url=None):
        if not url:
            return
        guard_instance = ThirdApiGuard(ie, url)
        try:
            guard_instance.check_and_save_frequency(url)
        except Exception:
            ie.report_msg(f'guard file: {guard_instance.data_file}')
            raise

    def __init__(self, ie, key=None):
        self.data_file = os.path.join(tempfile.gettempdir(), 'third_api_guard.json')
        self.disable_third_api = ie._downloader.params.get('disable_third_api', False)
        if not self.disable_third_api:
            env_disable_third_api = os.getenv('DISABLE_THIRD_API', None) or os.getenv('disable_third_api', None)
            if env_disable_third_api and (env_disable_third_api.lower() == 'true' or env_disable_third_api.lower() == '1'):
                self.disable_third_api = True
        self.key = key
        self.ie = ie

    def check_and_save_frequency(self, key=None):
        if self.disable_third_api:
            self.ie.report_warning('third api is disabled')
            raise ExtractorError('third api is disabled')
        if not self._check_and_save_frequency_safely(key):
            self.ie.report_warning('third api is too frequent')
            raise ExtractorError('third api is too frequent')

    def _check_and_save_frequency_safely(self, key=None):
        try:
            if not key:
                key = self.key
            if not key:
                return False

            existing_data = {}
            try:
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                self.ie.write_debug('lock file: r <_save_set_last_third_api_time>')
                with locked_file(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        existing_data = json.loads(content)
            except Exception:
                pass
            finally:
                self.ie.write_debug('unlock file: r <_save_set_last_third_api_time>')

            now_time = int(time.time())
            last_time = existing_data.get(key)
            if last_time:
                time_diff = now_time - last_time
                if time_diff < 60 * 10:
                    return False

            if not existing_data or len(existing_data) >= 30:
                existing_data = {}
            existing_data[key] = now_time
            self.ie.write_debug('lock file: w <_save_set_last_third_api_time>')
            with locked_file(self.data_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(existing_data))
            self.ie.write_debug('unlock file: w <_save_set_last_third_api_time>')
            return True
        except Exception:
            return True
