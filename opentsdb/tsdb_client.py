import logging
import queue
import socket
import string
import threading
import time
from os import environ
from typing import Optional

from opentsdb.exceptions import ValidationError
from opentsdb.metrics import Metric
from opentsdb.protocols import TSDBConnectProtocols

logger = logging.getLogger('opentsdb-py')


class TSDBClient:
    TSDB_HOST = environ.get('OPEN_TSDB_HOST', '127.0.0.1')
    TSDB_PORT = int(environ.get('OPEN_TSDB_PORT', 4242))
    TSDB_URI = environ.get('OPEN_TSDB_URI')
    TSDB_PUT_ENDPOINT = environ.get('OPEN_TSDB_PUT_ENDPOINT', '/api/put?details=true')
    TSDB_VERSION_ENDPOINT = environ.get('OPEN_TSDB_VERSION_ENDPOINT', '/api/version')

    TSDB_MAX_METRICS_QUEUE_SIZE = int(environ.get('TSDB_MAX_METRICS_QUEUE_SIZE', 10000))
    TSDB_SEND_METRICS_PER_SECOND_LIMIT = int(environ.get('TSDB_SEND_METRICS_PER_SECOND_LIMIT', 1000))
    TSDB_SEND_METRICS_BATCH_LIMIT = int(environ.get('TSDB_SEND_METRICS_BATCH_LIMIT', 50))
    TSDB_DEFAULT_HTTP_COMPRESSION = environ.get('TSDB_DEFAULT_HTTP_COMPRESSION', 'gzip')
    VALID_METRICS_CHARS = set(string.ascii_letters + string.digits + '-_./')

    def __init__(
            self,
            host: str = TSDB_HOST,
            port: int = TSDB_PORT,
            check_tsdb_alive: bool = False,
            protocol: str = TSDBConnectProtocols.HTTP,
            run_at_once: bool = True,
            static_tags: dict = None,
            host_tag: bool = True,
            max_queue_size: int = TSDB_MAX_METRICS_QUEUE_SIZE,
            http_compression: str = TSDB_DEFAULT_HTTP_COMPRESSION,
            uri: str = TSDB_URI,
            send_metrics_limit: int = TSDB_SEND_METRICS_PER_SECOND_LIMIT,
            send_metrics_batch_limit: int = TSDB_SEND_METRICS_BATCH_LIMIT,
            put_endpoint: str = TSDB_PUT_ENDPOINT,
            version_endpoint: str = TSDB_VERSION_ENDPOINT,
    ):

        self.host_tag = host_tag
        self.protocol = protocol
        self.check_tsdb_alive = check_tsdb_alive
        self.static_tags = static_tags or {}
        self.send_metrics_limit = send_metrics_limit if protocol == TSDBConnectProtocols.TELNET else 0
        self.send_metrics_batch_limit = send_metrics_batch_limit if protocol == TSDBConnectProtocols.HTTP else 0
        self.http_compression = http_compression

        self._tsdb_connect = None
        self._close_client = threading.Event()
        self._metrics_queue = queue.Queue(maxsize=max_queue_size)
        self.statuses = {'success': 0, 'failed': 0, 'queued': 0}

        self._metric_send_thread = None

        if run_at_once is True:
            self.init_client(host, port, uri, put_endpoint, version_endpoint)

    def init_client(
            self, host, port: int = TSDB_PORT, uri: Optional[str] = None,
            put_endpoint: str = TSDB_PUT_ENDPOINT,
            version_endpoint: str = TSDB_VERSION_ENDPOINT
    ):
        self._tsdb_connect = TSDBConnectProtocols.get_connect(
            self.protocol, host, port, self.check_tsdb_alive,
            compression=self.http_compression, uri=uri,
            put_endpoint=put_endpoint, version_endpoint=version_endpoint
        )

        self._metric_send_thread = TSDBConnectProtocols.get_push_thread(
            self.protocol, self._tsdb_connect, self._metrics_queue, self._close_client,
            self.send_metrics_limit, self.send_metrics_batch_limit, self.statuses)
        self._metric_send_thread.daemon = True
        self._metric_send_thread.start()

        self._load_predefined_metrics()

    def _load_predefined_metrics(self):
        for key, value in self.__class__.__dict__.items():
            if isinstance(value, Metric):
                self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if isinstance(value, Metric):
            if value.client is None:
                value.client = self

        super(TSDBClient, self).__setattr__(key, value)

    def is_connected(self) -> bool:
        return self._metric_send_thread.is_alive()

    def is_alive(self) -> bool:
        return self._tsdb_connect.is_alive()

    def close(self, force=False):
        self._close_client.set()
        self._metrics_queue.put(StopIteration)
        if force and self._tsdb_connect:
            self._tsdb_connect.stopped.set()

    def wait(self):
        while self.is_connected():
            time.sleep(0.05)

    def queue_size(self) -> int:
        return self._metrics_queue.qsize()

    def send(self, name: str, value, **tags) -> dict:
        tags.update(self.static_tags)
        if self.host_tag is True and 'host' not in tags:
            tags['host'] = socket.gethostname()

        self._validate_metric(name, value, tags)
        metric = dict(metric=name, timestamp=int(tags.pop('timestamp', time.time())), value=value, tags=tags)

        if not self._close_client.is_set():
            self._push_metric_to_queue(metric)

        return metric

    def _validate_metric(self, name, value, tags):
        try:
            assert all(char in self.VALID_METRICS_CHARS for char in name), \
                "Metric name contain incorrect chars '%s'" % name
            assert isinstance(value, (str, int, float)), "Incorrect metric value type '%s'" % type(value)
            assert tags != {}, "Need at least one tag"
        except AssertionError as error:
            raise ValidationError("Metric not valid: %s" % str(error))

    def _push_metric_to_queue(self, metric):
        try:
            self._metrics_queue.put(metric, False)
        except queue.Full:
            logger.warning("Drop oldest metric because Queue is full.")
            self._metrics_queue.get()
            self._metrics_queue.put(metric, False)

        self.statuses['queued'] += 1
