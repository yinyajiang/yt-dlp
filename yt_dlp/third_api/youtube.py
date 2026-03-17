from yt_dlp.third_api.extractor.snap_mutil_rapidapi import SnapMutilRapidApi
from .extractor import YoutubeRapidApi, ThirdApiGuard, AllInOneMutilRapidApi


class YoutubeThirdIE:
    def __init__(self, ie):
        self.ie = ie

    def extract_video_info(self, video_id, url, prefer_downloaded=True):
        ThirdApiGuard.guard(self.ie, f'youtube-{video_id}')
        return extract_youtube_video_info(self.ie, video_id, url, prefer_downloaded)


def extract_youtube_video_info(ie, video_id, url, prefer_downloaded=True):
    if prefer_downloaded:
        try:
            return YoutubeRapidApi(ie).extract_video_info(video_id, check_fmt_url=False)
        except Exception as e:
            if 'You have exceeded' in str(e):
                return AllInOneMutilRapidApi(ie).extract_video_info(url, check_fmt_url=True)
            raise
    else:
        try:
            return AllInOneMutilRapidApi(ie).extract_video_info(url, check_fmt_url=True)
        except Exception:
            SnapMutilRapidApi(ie).extract_video_info(url, video_id)
