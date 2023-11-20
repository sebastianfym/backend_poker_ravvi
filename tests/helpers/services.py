from subprocess import Popen, DEVNULL
import signal

class Services:
    engine = None
    api = None
    ws = None

    names = ['engine','api','ws']

    @classmethod
    def start_subprocess(cls, cmd):
        return Popen(cmd, shell=True, stderr=DEVNULL, stdout=DEVNULL)
    
    @classmethod
    def stop_subprocess(cls, handle):
        if not handle:
            return
        handle.send_signal(signal.SIGINT)
        return handle.wait()
    
    @classmethod
    def start_service(cls, name):
        if getattr(cls, name):
            return
        cmd = f"ravvi_poker_{name} --log-debug --log-file {name}.log run"
        handle = cls.start_subprocess(cmd)
        setattr(cls, name, handle)

    @classmethod
    def stop_service(cls, name):
        handle = getattr(cls, name)
        if not handle:
            return
        exitcode = cls.stop_subprocess(handle)
        setattr(cls, name, None)

    @classmethod
    def start(cls):
        for name in cls.names:
            cls.start_service(name)

    @classmethod
    def stop(cls):
        for name in cls.names:
            cls.stop_service(name)
