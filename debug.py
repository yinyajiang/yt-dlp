import json
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
debug_dir = os.path.join(current_dir, 'debug')
os.makedirs(debug_dir, exist_ok=True)

os.environ['hikerapi_key'] = ''
os.environ['rapidapi_key'] = ''
os.environ['webview_location'] = ''
# os.environ['webview_params'] = ''
os.environ['webview_downpage_params'] = ''
os.environ['mp4decrypt_location'] = os.path.join(debug_dir, 'mp4decrypt')


# import yt_dlp
# sys.argv = [
#   os.path.join(current_dir, "yt-dlp"),
#    "--ffmpeg-location", debug_dir,
#    "--mp4decrypt-location", os.path.join(debug_dir, "mp4decrypt"),
#    "--legacy-server-connect",
#    "--no-check-certificates",
#    "--no-colors",
#    "-J",
#    "--skip-download",
#    "--yes-playlist",
#    "--flat-playlist",
#    #"--allow-unplayable-formats",
#    #"--extractor-args",
#    'https://www.tvbanywherena.com/cantonese/videos/437-SuperTrioShow/6007674088001'
# ]
# yt_dlp.main()

from yt_dlp import YoutubeDL

ydl = YoutubeDL({
    # 'cookiefile': os.path.join(debug_dir, 'cookies.txt'),
    # 'ignoreerrors': True,
    # 'plain_entries': True,
    # 'skip_download_media_type': "",
    # "progress_template": {
    #     'download':r'{"status": "%(progress.status)s","n_entries": %(info.n_entries)s, "playlist_index": %(info.playlist_index)s}',
    # },
    # 'load_info_filename':"",
    # 'mp4decrypt_location': os.path.join(debug_dir, 'mp4decrypt'),
    'ffmpeg_location': debug_dir,
    # 'noplaylist':True,
    'outtmpl': f'{debug_dir}/downloads/%(id)s.%(ext)s',
    'extract_flat': 'in_playlist',
    'nopart': True,
    'http_headers': {
        # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        # "Accept": "*/*",
    },
    # "proxy": '',
    'no_check_certificate': True,
    # "ignoreerrors":True,
    'allow_unplayable_formats': True,
    # 'webview_location': '/Users/new/Documents/GitHub/webviewloader/webinterceptor/dist/WebVideoDownloader.app',
    # 'webview_params': '',
    # 'webview_downpage_params': 'downpage --url {url} --path {file}',
    'force_use_webview': False,
    'verbose': True,
    'restrictfilenames': True,
    'progress_with_newline': True,
    # "format": "audio-192p",
    'ignore_postproc_errors': True,
    'source_address': '',
    # 'proxy': '',
    'keepvideo': True,
    'extractor_args': {
        'onlyfans': {
            'external_ie': ['18209'],
        },
        'instagram': {
            'hikerapi_key': ['ZXMO9mnHA1MOSD56TSKzrWJPNrNnw23D'],
            # 'hikerapi_not_prefer_video': [True],
        },
        # 'generic': {
        #     'dumphtml': [True],
        # },
        'youtube': {
            # "formats": ["missing_pot"],
            'player_client': [
                # "android_vr",
                # 'web_safari',
                # 'web',
                # 'web_creator',
                # 'web_embedded',
                # 'android',
                # 'android_creator',
                # 'ios',
                # 'ios_creator',
                # 'mweb',
                # 'tv',
            ],
            # 'player_skip': ['webpage'],
            # 'po_token': ['all+MnTTeU8sGQrkKNNBHG16V49DYe5x5Eg7GmkcAPdDnPrTAzHMPF8kvrIbb-6imeNJXb5UVR1o7Pzg9MqRbGzZWCr7By4gTNFekiye4MafChlGBHoizQ7bKMgppnREIY9FKpn4EyOK8mvsZpQWvba07q9FJMOoeg=='],
            # 'visitor_data': ['Cgs4MTRNVGVDWmtzbyiRwKG8BjIKCgJISxIEGgAgWw%3D%3D'],
            # 'potoken_webview_location': ['/Users/new/Documents/GitHub/webviewloader/webview/dist/LOGIN.app/Contents/MacOS/LOGIN'],
            # 'potoken_webview_params': [r'{page_url} --hidden --run-js-file {js_file}'],
            # 'potoken_cmd_location': [r'/Users/new/Documents/MMProject/videodownloader/go-videodownload-cli/videodownload'],
            # 'potoken_cmd_params': [r'get-potoken'],
            'prefer_rapidapi': [False],
            'only_rapidapi': [False],
            'rapidapi_key': [
                # '04ce9a4844mshd1578c7feea684ep1eab36jsndf9a6b522f3c',
                # 'rapidapi_host': ['youtube-rapidapi.p.rapidapi.com'],
                # 'rapidapi_endpoint': ['https://youtube-rapidapi.p.rapidapi.com/video/info'
            ],
        },
    },
    # 'skip_download': True,
    # 'dumpjson':True,
},
)

# ydl.download_with_info_file(os.path.join(current_dir, 'debug', 'info.json'))

#
# 'https://www.msn.com/en-us/video/news/lafd-chief-slams-budget-cuts-says-department-was-let-down/vi-BB1rfd5y?ocid=winp2fptaskbarhover#details'

# info = ydl.extract_info_use_thirdapi('https://www.youtube.com/watch?v=OJ_W4R0WBdU',
#                                      third_api='allinone_mutil_rapidapi',
#                                      download=False,
#                                      force_generic_extractor=False)

info = ydl.extract_info('https://www.facebook.com/watch?v=957463283129708',
                        download=False,
                        force_generic_extractor=False)

s = json.dumps(ydl.sanitize_info(info))
print(s)
with open(os.path.join(current_dir, 'debug', 'info.json'), 'w') as f:
    f.write(s)
# ydl.download_with_info_file(os.path.join(current_dir, 'debug', 'info.json'))
