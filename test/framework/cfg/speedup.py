_speedup = 1


def select_speedup(speedup):
    """speedup is used by the mock api"""
    global _speedup
    _speedup = speedup


def speedup():
    return _speedup
