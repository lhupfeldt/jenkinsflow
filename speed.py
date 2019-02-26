"""Move time and sleep to api class, so that the MockApi can speed up time."""


import time as real_time


class Speed():
    speedup = 1

    def time(self):
        return real_time.time()

    def sleep(self, seconds):
        return real_time.sleep(seconds)
