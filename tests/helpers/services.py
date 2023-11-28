import logging
from subprocess import Popen, DEVNULL
import signal
import time

log = logging.getLogger(__name__)

class Services:
    engine = None
    api = None
    ws = None

    names = ['engine','api','ws']

    @classmethod
    def start_subprocess(cls, cmd):
        return Popen(cmd, shell=True, stdout=DEVNULL)
    
    @classmethod
    def stop_subprocess(cls, handle):
        if not handle:
            return
        handle.send_signal(signal.SIGTERM)
        return handle.wait()
    
    @classmethod
    def start_service(cls, name):
        if getattr(cls, name):
            return
        cmd = f"coverage run --data-file=.coverage.{name} --rcfile=.coveragerc -m ravvi_poker.{name}.cli --log-file {name}.log run"
        handle = cls.start_subprocess(cmd)
        log.info('service %s started', name)
        setattr(cls, name, handle)

    @classmethod
    def stop_service(cls, name):
        handle = getattr(cls, name)
        if not handle:
            return
        exitcode = cls.stop_subprocess(handle)
        log.info('service %s stopped', name)
        setattr(cls, name, None)

    @classmethod
    def start(cls):
        for name in cls.names:
            cls.start_service(name)
        time.sleep(3)

    @classmethod
    def stop(cls):
        for name in cls.names:
            cls.stop_service(name)
