import urllib.parse


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
    for s in hint.split('.'):
        if s:
            return s in [site.lower() for site in support_sites]
    return False
