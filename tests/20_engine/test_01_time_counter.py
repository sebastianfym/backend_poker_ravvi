import pytest
import time
from ravvi_poker.engine.time import TimeCounter

@pytest.mark.skip
def test_time_counter():
    def check_value(value, expected, delta):
        #print(value)
        return abs(value-expected)<delta

    x = TimeCounter()
    assert x.total_seconds == 0
    assert not x.running

    x.start() 
    assert x.running
    assert check_value(x.total_seconds, 0, 0.1)

    time.sleep(2)
    assert check_value(x.total_seconds, 2, 0.1)
    
    time.sleep(1)
    assert check_value(x.total_seconds, 3, 0.1)

    x.stop()
    assert not x.running
    assert check_value(x.total_seconds, 3, 0.1)

    time.sleep(2)
    assert not x.running
    assert check_value(x.total_seconds, 3, 0.1)

    x.start() 
    assert x.running
    assert check_value(x.total_seconds, 3, 0.1)

    time.sleep(2)
    assert check_value(x.total_seconds, 5, 0.1)
    
    time.sleep(1)
    assert check_value(x.total_seconds, 6, 0.1)

    x.stop()
    assert not x.running
    assert check_value(x.total_seconds, 6, 0.1)

if __name__=='__main__':
    test_time_counter()