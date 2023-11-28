import logging
import pytest

from helpers.services import Services

log = logging.getLogger(__name__)

@pytest.fixture(autouse=True, scope='session')
def services():
    Services.start()
#    log.info('SERVICES START')
    yield
#    log.info('SERVICES STOP')
    Services.stop()