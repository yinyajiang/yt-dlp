from .extractor import YoutubeRapidApi, ThirdApiGuard, AllInOneMutilRapidApi


class YoutubeThirdIE:
    def __init__(self, ie):
        self.ie = ie

    def extract_video_info(self, video_id, url):
        ThirdApiGuard.guard(self.ie, f'youtube-{video_id}')
        try:
            return YoutubeRapidApi(self.ie).extract_video_info(video_id, check_fmt_url=False)
        except Exception as e:
            if 'You have exceeded' in str(e):
                return AllInOneMutilRapidApi(self.ie).extract_video_info(url, check_fmt_url=True)
            raise
