import time


class _HyperSpeed(object):
    def __init__(self, speedup):
        self.speedup = speedup

    def time(self):
        return time.time() * self.speedup

    def sleep(self, seconds):
        return time.sleep(seconds / self.speedup)
