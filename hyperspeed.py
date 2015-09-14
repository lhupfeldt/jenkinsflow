import time as real_time


_speedup = 1


def set_speedup(speedup):
    global _speedup
    assert isinstance(speedup, int)
    _speedup = speedup

    
def mocked():
    return _speedup != 1


def get_speedup():
    return _speedup


def time():
    if _speedup == 1:
        return real_time.time()
    return real_time.time() * _speedup


def sleep(seconds):
    if _speedup == 1:
        return real_time.sleep(seconds)
    return real_time.sleep(seconds / float(_speedup))
