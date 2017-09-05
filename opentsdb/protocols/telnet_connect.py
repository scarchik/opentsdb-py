import logging
import socket
import time

from opentsdb.protocols.tsdb_connect import TSDBConnect
from opentsdb.exceptions import TSDBNotAlive

logger = logging.getLogger('opentsdb-py')


class TelnetTSDBConnect(TSDBConnect):

    def is_alive(self, timeout=3, raise_error=False) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.tsdb_host, self.tsdb_port))
            sock.close()
        except (ConnectionRefusedError, socket.timeout) as error:
            if raise_error:
                raise TSDBNotAlive(str(error))
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
        attempt = 0
        while not self.stopped.is_set():
            try:
                self._connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connect.settimeout(timeout)
                self._connect.connect((self.tsdb_host, self.tsdb_port))
                return
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(min(15, 2 ** attempt))
                attempt += 1

    def sendall(self, metric: dict):
        try:
            tags_string = ' '.join(['%s=%s' % (key, value) for key, value in metric['tags'].items()])
            metric_str = "put %s %d %s %s\n" % (metric['metric'], metric['timestamp'], metric['value'], tags_string)
            logger.debug("Send metric: %s", metric_str)
            self.connect.sendall(metric_str.encode('utf-8'))
        except Exception:
            self._connect.close()
            raise
