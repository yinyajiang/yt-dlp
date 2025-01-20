import requests
import re
import os
import tempfile
import zlib
from ._compressed_potoken_js_files import js_files


def get_decompress_po_token_js(name):
    try:
        compressed = js_files()[name]
        return zlib.decompress(compressed).decode('utf-8')
    except Exception:
        return None


def has_compressed_potoken_js():
    return bool(js_files())


class PoToken:
    PAGE_URL = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'

    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.',
        'accept-language': 'en-US;q=0.9',
        'user-agent': USER_AGENT,
    }

    @staticmethod
    def _get_visitor_data():
        response = requests.get(PoToken.PAGE_URL, headers=PoToken.HEADERS)
        response.raise_for_status()

        pattern = r'"visitorData"\s*:\s*"([^"]+)'
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)
        raise ValueError('No visitor data found')

    @staticmethod
    def _gen_po_token_js(visitor_data):
        try:
            js_prefix = f'''
                Object.defineProperty(window.navigator, 'userAgent', {{ value: '{PoToken.USER_AGENT}', writable: false }});
                window.visitorData = '{visitor_data}';
                window.onPoToken = (poToken) => {{
                    let result = {{
                        'poToken': poToken,
                        'visitorData': window.visitorData,
                    }};
                    let str_result = JSON.stringify(result);
                    pywebview.api.result(str_result);
                }};
            '''

            inject_js = get_decompress_po_token_js('inject.js')
            base_js = get_decompress_po_token_js('base.js')
            if not inject_js or not base_js:
                raise ValueError('Failed to get inject.js or base.js')

            pattern = r'}\s*\)\(_yt_player\);\s*$'
            base_js = re.sub(pattern, f';{inject_js};\\g<0>', base_js)

            temp_file = os.path.join(tempfile.gettempdir(), 'temp_inject.js')
            with open(temp_file, 'w') as f:
                f.write(js_prefix + base_js)

            return temp_file

        except Exception as e:
            print(f'Error generating po token js: {e!s}')
            raise

    @staticmethod
    def gen_po_token_run_params():
        try:
            if not has_compressed_potoken_js():
                return None
            visitor_data = PoToken._get_visitor_data()
            return {
                'js_file': PoToken._gen_po_token_js(visitor_data),
                'page_url': PoToken.PAGE_URL,
                'user_agent': PoToken.USER_AGENT,
                'headers': PoToken.HEADERS,
            }
        except Exception:
            return None


def gen_po_token_run_params():
    return PoToken.gen_po_token_run_params()
