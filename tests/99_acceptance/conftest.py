import logging
import pytest

from tests.helpers.services import Services

log = logging.getLogger(__name__)

@pytest.fixture(autouse=True, scope='session')
def services():
    Services.start()
    yield
    Services.stop()