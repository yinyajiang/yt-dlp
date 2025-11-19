from .extractor import YoutubeRapidApi, ThirdApiGuard


class YoutubeThirdIE:
    def __init__(self, ie):
        self.ie = ie

    def extract_video_info(self, video_id):
        ThirdApiGuard.guard(self.ie, f'youtube-{video_id}')
        return YoutubeRapidApi(self.ie).extract_video_info(video_id)
