import urllib.parse
from ...utils import remove_query_params


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
