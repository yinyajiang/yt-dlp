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
