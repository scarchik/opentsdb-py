import logging
import json
import gzip

from requests import Session

from opentsdb.protocols.tsdb_connect import TSDBConnect

logger = logging.getLogger('opentsdb-py')


class TSDBUrls:

    def __init__(self, host: str, port: int):
        self.version = 'http://%s:%s/api/version' % (host, port)
        self.put = 'http://%s:%s/api/put?details=true' % (host, port)


class HttpTSDBConnect(TSDBConnect):

    SEND_TIMEOUT = 2

    def __init__(self, host: str, port: int, *args, **kwargs):
        super().__init__(host, port, *args, **kwargs)
        self.tsdb_urls = TSDBUrls(host, int(port))
        assert self.compression in ['gzip', None], 'Unsupported HTTP compression type: %s' % self.compression
        if self.compression:
            logger.info("Compression %s is enabled", self.compression)

    def is_alive(self, timeout=3, raise_error=False) -> bool:
        try:
            response = self.connect.get(self.tsdb_urls.version, timeout=timeout)
            if response.status_code != 200:
                raise ConnectionError("Bad status code")
            return True
        except Exception as error:
            if raise_error:
                raise error
            return False

    @property
    def connect(self) -> Session:
        if not self._connect:
            self._connect = Session()
            if self.compression:
                self._connect.headers.update({'Content-Encoding': self.compression})
        return self._connect

    def sendall(self, *metrics) -> dict:
        logger.debug("Send metrics:\n %s", '\n'.join(str(m) for m in metrics))
        response = self.connect.post(
            self.tsdb_urls.put,
            data=gzip.compress(json.dumps(metrics).encode()) if self.compression else json.dumps(metrics),
            timeout=self.SEND_TIMEOUT)
        return response.json()
