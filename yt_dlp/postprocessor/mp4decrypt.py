import contextvars
import os
import subprocess
from .common import PostProcessor


class MP4DecryptPP(PostProcessor):
    _mp4decrypt_location = contextvars.ContextVar('mp4decrypt_location', default=None)

    def __init__(self, downloader=None):
        PostProcessor.__init__(self, downloader)
        self._path = self.get_param('mp4decrypt_location', self._mp4decrypt_location.get())

    def run(self, info):
        files = self._get_files_from_info(info)
        for f in files:
            dl_path, _ = os.path.split(info['filepath'])
            inputpath = os.path.join(info.get('__finaldir', dl_path), f)
            self._decrypt(info['_drm_decrypt_key'], inputpath)
        return [], info

    def can_decrypt(self, info):
        return info.get('_drm_decrypt_key', None)

    @property
    def available(self):
        return self._path and os.path.exists(self._path)

    def _decrypt(self, decrypt_key, inputpath):
        self.to_screen(f'Decrypting {inputpath}')
        if not os.path.exists(inputpath):
            self.report_warning(f'File not found: {inputpath}')
            return
        basename = os.path.basename(inputpath)
        temp_outputpath = os.path.join(os.path.dirname(inputpath),
                                       os.path.splitext(basename)[0] + '_de' + os.path.splitext(basename)[1])
        try:
            subprocess.run([self._path, '--key', decrypt_key, inputpath, temp_outputpath]).check_returncode()
            os.remove(inputpath)
            os.rename(temp_outputpath, inputpath)
        except Exception as e:
            self.report_warning(f'Decrypt failed: {e}')

    def _get_files_from_info(self, info_dict):
        files_to_move = info_dict.get('__files_to_move', {})
        files_to_merge = info_dict.get('__files_to_merge', [])
        if isinstance(files_to_move, dict):
            files_to_move = files_to_move.keys()
        if isinstance(files_to_merge, dict):
            files_to_merge = files_to_merge.keys()
        return set(files_to_move) | set(files_to_merge)
