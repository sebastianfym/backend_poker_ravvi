import inspect
import logging
from ravvi_poker.utils.utc import now_utc, DateTime

logger = logging.getLogger(__name__)


def check_func_args(f1, f2):
    s1 = inspect.getfullargspec(f1)
    logger.debug(s1)
    s2 = inspect.getfullargspec(f2)
    logger.debug(s2)
    assert s1==s2

def check_timestamp_threshold(ts: DateTime, threshold_seconds=10):
    utc = now_utc()
    diff_seconds = (ts-utc).total_seconds()
    return abs(diff_seconds) < threshold_seconds