import logging
import signal

logger = logging.getLogger(__name__)


class SignalHandler(object):
    def __init__(self, callback=None, signals=None):
        if not signals:
            signals = [signal.SIGINT, signal.SIGTERM, signal.SIGABRT]
        for sig in signals:
            signal.signal(sig, self.signal_handler)
        self._callback = callback

    def signal_handler(self, signum, frame):
        if self._callback:
            self._callback(signum)
