from datetime import datetime as DateTime
from datetime import timezone

def now_utc() -> DateTime:
    return DateTime.now(timezone.utc).replace(tzinfo=None)

