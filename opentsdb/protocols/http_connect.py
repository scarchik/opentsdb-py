import logging
import json
import gzip
import os.path
from typing import Optional

from requests import Session

from opentsdb.protocols.tsdb_connect import TSDBConnect
from opentsdb.exceptions import TSDBNotAlive

logger = logging.getLogger('opentsdb-py')


class TSDBUrls:

    def __init__(self, base_url, version_endpoint, put_endpoint):
        self.version = base_url + version_endpoint
        self.put = base_url + put_endpoint

    @classmethod
    def from_host_and_port(cls, host, port, version_endpoint, put_endpoint):
        base_url = 'http://{}:{}'.format(host, port)
        return cls(base_url, version_endpoint, put_endpoint)

    @classmethod
    def from_uri(cls, uri, version_endpoint, put_endpoint):
        return cls(uri, version_endpoint, put_endpoint)


class HttpTSDBConnect(TSDBConnect):
    SEND_TIMEOUT = 2

    def __init__(self, host: str, port: int, check_tsdb_alive: bool,
                 compression: str, version_endpoint: str, put_endpoint: str, uri: Optional[str]):
        if uri is None:
            self.tsdb_urls = TSDBUrls.from_host_and_port(host, int(port), version_endpoint, put_endpoint)
        else:
            self.tsdb_urls = TSDBUrls.from_uri(uri, version_endpoint, put_endpoint)
        super().__init__(host, port, check_tsdb_alive)
        self.compression = compression
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
                raise TSDBNotAlive(str(error))
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
