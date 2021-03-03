import time
from functools import wraps


def rate_limit(cps):
    def dec(func):
        last_time = [time.time()]

        @wraps(func)
        def cps_decorator(*args, **kwargs):
            t = time.time()
            if (t - last_time[0]) < 1.0/cps:
                return
            last_time[0] = t
            return func(*args, **kwargs)
        return cps_decorator
    return dec
