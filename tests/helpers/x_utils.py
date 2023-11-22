import inspect
import logging

logger = logging.getLogger(__name__)


def check_func_args(f1, f2):
    s1 = inspect.getfullargspec(f1)
    logger.debug(s1)
    s2 = inspect.getfullargspec(f2)
    logger.debug(s2)
    assert s1==s2
