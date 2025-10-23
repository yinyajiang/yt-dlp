from .extractor import SnapMutilRapidApi, AllInOneMutilRapidApi, ZMMutilRapidApi
from ..utils import ExtractorError


class MutilThirdIE:
    API_NAME = 'mutil_api'

    cls_ies = [
        AllInOneMutilRapidApi,
        SnapMutilRapidApi,
        ZMMutilRapidApi,
    ]

    def __init__(self, ie):
        self.ie = ie

    @classmethod
    def is_supported_site(cls, hint):
        return any(ie_cls.is_supported_site(hint) for ie_cls in cls.cls_ies)

    def extract_video_info(self, video_url, video_id=None):
        ies = [ie_cls(self.ie) for ie_cls in self.cls_ies if ie_cls.is_supported_site(video_url)]
        if not ies:
            raise ExtractorError('MutilThirdIE: No supported')
        first_exception = None
        for ie in ies:
            try:
                self.ie.report_msg(f'try to use {ie.__class__.__name__} to extract video info.')
                return ie.extract_video_info(video_url, video_id)
            except Exception as e:
                self.ie.report_msg(f'use {ie.__class__.__name__} failed: {e}.')
                first_exception = e
                continue
        raise first_exception
