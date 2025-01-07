import json
import os


current_dir = os.path.dirname(os.path.realpath(__file__))
debug_dir = os.path.join(current_dir, "debug")
os.makedirs(debug_dir, exist_ok=True)

# import yt_dlp
# sys.argv = [
#   os.path.join(current_dir, "yt-dlp"),
#    "--ffmpeg_location", debug_dir,
#    "--mp4decrypt_location", os.path.join(debug_dir, "mp4decrypt"),
#    "--legacy-server-connect",
#    "--no-check-certificates",
#    "--no-colors",
#    "-J",
#    "--skip-download",
#    "--yes-playlist",
#    "--flat-playlist",
#    "--allow-unplayable-formats",
#    "--extractor-args",
#    "url"
# ]
# yt_dlp.main()

from yt_dlp import YoutubeDL

ydl = YoutubeDL({
    # "cookiefile":'',
    # 'ignoreerrors': True,
    # 'plain_entries': True,
    # 'skip_download_media_type': "",
    # "progress_template": {
    #     'download':r'{"status": "%(progress.status)s","n_entries": %(info.n_entries)s, "playlist_index": %(info.playlist_index)s}',
    # },
    # 'load_info_filename':"",
    'mp4decrypt_location': os.path.join(debug_dir, "mp4decrypt"),
    'ffmpeg_location': debug_dir,
    # 'noplaylist':True,
    # 'outtmpl': "",
    'extract_flat': True,
    'nopart': True,
    'http_headers': {
        # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        # "Accept": "*/*",
    },
    # "proxy": '',
    'no_check_certificate': True,
    # "ignoreerrors":True,
    'allow_unplayable_formats': True,
    'webview_location': '',
    'webview_params': '',
    'force_use_webview': False,
    # 'verbose':True,
    'restrictfilenames': True,
    'progress_with_newline': True,
    # "format": "hls-fastly_skyfire-301",
    'ignore_postproc_errors': True,
    'extractor_args': {
        'onlyfans': {
            'external_ie': ['18209'],
        },
        'youtube': {
            # "formats": ["missing_pot"],
            'player_client': [
                # "android_vr"
                # 'all'
                #  web_embedded',
            ],
            # 'player_skip': ['configs'],
            'po_token': [],
            'visitor_data': [],
        },
    },
},
)

# ydl.download_with_info_file(os.path.join(current_dir, "debug", "info.json"))
info = ydl.extract_info('url', download=False)
s = json.dumps(ydl.sanitize_info(info))
print(s)
with open(os.path.join(current_dir, 'debug', 'info.json'), 'w') as f:
    f.write(s)
