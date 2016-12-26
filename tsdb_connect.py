import threading
import logging
import socket
import time

logger = logging.getLogger('opentsdb-py')


class TSDBConnect:

    def __init__(self, host: str, port: int, check_tsdb_alive: bool=False):
        self.tsdb_host = host
        self.tsdb_port = port

        if check_tsdb_alive:
            self.is_alive(raise_error=True)

        self._connect = None
        self.stopped = threading.Event()

    def is_alive(self, timeout=3, raise_error=False) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.tsdb_host, self.tsdb_port))
            sock.close()
        except (ConnectionRefusedError, socket.timeout):
            if raise_error is True:
                raise
            return False
        else:
            return True

    @property
    def connect(self) -> socket.socket:
        if not self._connect or getattr(self._connect, '_closed', False) is True:
            logger.debug("Connect to OpenTSDB: %s:%s", self.tsdb_host, self.tsdb_port)
            self.stopped.clear()
            self._make_connection()

        return self._connect

    def _make_connection(self, timeout=2):
        self._connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect.settimeout(timeout)
        attempt = 0
        while not self.stopped.is_set():
            try:
                self._connect.connect((self.tsdb_host, self.tsdb_port))
                return
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(min(15, 2 ** attempt))
                attempt += 1

    def disconnect(self):
        logger.debug("Disconnecting from %s:%s", self.tsdb_host, self.tsdb_port)
        self.stopped.set()
        if self._connect:
            self._connect.close()
        self._connect = None

    def sendall(self, line: bytes):
        self.connect.sendall(line)
