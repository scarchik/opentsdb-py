import threading
import logging

logger = logging.getLogger('opentsdb-py')


class TSDBConnect:

    def __init__(self, host: str, port: int, check_tsdb_alive: bool=False, *args, **kwargs):
        self.tsdb_host = host
        self.tsdb_port = int(port)
        self._connect = None

        if check_tsdb_alive:
            self.is_alive(raise_error=True)

        self.stopped = threading.Event()

    def is_alive(self, timeout=3, raise_error=False) -> bool:
        raise NotImplementedError()

    @property
    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        logger.debug("Disconnecting...")
        self.stopped.set()
        if self._connect:
            self._connect.close()
        self._connect = None

    def sendall(self, metric: dict):
        raise NotImplementedError()
