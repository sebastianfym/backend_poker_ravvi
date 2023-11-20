import logging
import pytest

logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True, scope='session')
def api_service():
    logger.info('start api service')
    yield
    logger.info('stop api service')
