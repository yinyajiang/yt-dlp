import zlib
import os
import sys


def compress_file(filename):
    with open(filename, encoding='utf-8') as f:
        data = f.read()
    return zlib.compress(data.encode('utf-8'))


if __name__ == '__main__':
    cur_dir = os.path.join(os.path.dirname(__file__))
    dest = os.path.abspath(os.path.join(cur_dir, '..', 'yt_dlp', 'utils', '_compressed_potoken_js_files.py'))

    if len(sys.argv) > 1 and 'inner' in sys.argv[1].lower():
        base_js = compress_file(os.path.join(cur_dir, 'js_res', 'potoken', 'base.js'))
        inject_js = compress_file(os.path.join(cur_dir, 'js_res', 'potoken', 'inject.js'))
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('''
def js_files():
    return {
        "base.js": %s,
        "inject.js": %s
    }
''' % (repr(base_js), repr(inject_js)))
    else:
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('''
def js_files():
    return {}
''')
