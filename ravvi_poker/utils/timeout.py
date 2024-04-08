import time

class TimeOut:

    def __init__(self, timeout: int) -> None:
        self.threshold = time.monotonic() + timeout

    def __bool__(self):
        return time.monotonic() >= self.threshold

