from datetime import datetime, timedelta

class TimeCounter:
    
    def __init__(self) -> None:
        self._total = 0
        self._started = None

    @property
    def running(self) -> bool: 
        return self._started is not None
    
    @property
    def total_seconds(self) -> int:
        total = self._total
        if self._started:
            total += (self._now()-self._started).total_seconds()
        return total

    def start(self):
        if self._started:
            return
        self._started = self._now()

    def stop(self):
        if not self._started:
            return
        extra_seconds = (self._now()-self._started).total_seconds()
        self._total += extra_seconds
        self._started = None

    def _now(self) -> datetime:
        return datetime.utcnow().replace(microsecond=0)
    
