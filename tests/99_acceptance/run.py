import logging
import pytest

logger = logging.getLogger(__name__)

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    import os
    start_from = os.path.dirname(__file__)
    pytest.main([start_from])