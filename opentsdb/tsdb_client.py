import threading
import logging
import socket
import string
import queue
import time
from os import environ

from opentsdb.exceptions import MetricDuplicated, ValidationError
from opentsdb.tsdb_connect import TSDBConnect
from opentsdb.push_thread import PushThread
from opentsdb.metrics import Metric

logger = logging.getLogger('opentsdb-py')


class TSDBClient:
    TSDB_HOST = environ.get('OPEN_TSDB_HOST', '127.0.0.1')
    TSDB_PORT = environ.get('OPEN_TSDB_PORT', 4242)

    MAX_METRICS_QUEUE_SIZE = 10000
    SEND_METRICS_PER_SECOND_LIMIT = 1000
    VALID_METRICS_CHARS = set(string.ascii_letters + string.digits + '-_./')

    def __init__(self, host: str=TSDB_HOST, port: int=TSDB_PORT, check_tsdb_alive: bool=False,
                 static_tags: dict=None, host_tag: bool=True, test_mode: bool=False, raise_duplicate=True,
                 max_queue_size: int=MAX_METRICS_QUEUE_SIZE, send_metrics_limit: int=SEND_METRICS_PER_SECOND_LIMIT):
        self.host_tag = host_tag
        self.static_tags = static_tags or {}
        self.raise_duplicate = raise_duplicate

        self._tsdb_connect = TSDBConnect(host, port, check_tsdb_alive)
        self._close_client = threading.Event()

        self._last_metric = None
        self._metrics_queue = queue.Queue(maxsize=max_queue_size)

        self._metric_send_thread = PushThread(
            self._tsdb_connect, self._metrics_queue, self._close_client, send_metrics_limit, test_mode)
        self._metric_send_thread.daemon = True
        self._metric_send_thread.start()

    def __setattr__(self, key, value):
        if isinstance(value, Metric):
            if value.client is None:
                value.client = self

        super(TSDBClient, self).__setattr__(key, value)

    def is_connected(self) -> bool:
        return self._tsdb_connect.is_alive()

    def close(self):
        self._close_client.set()

    def wait(self):
        while self._metric_send_thread.is_alive():
            time.sleep(0.05)

    def stop(self):
        self._tsdb_connect.stopped.set()

    def queue_size(self) -> int:
        return self._metrics_queue.qsize()

    def send(self, name: str, value, **tags) -> str:
        tags.update(self.static_tags)
        if self.host_tag is True and 'host' not in tags:
            tags['host'] = socket.gethostname()

        self._validate_metric(name, value, tags)

        timestamp = int(tags.pop('timestamp', time.time()))
        tags_string = ' '.join(['%s=%s' % (key, value) for key, value in tags.items()])
        metric_str = "put %s %d %s %s\n" % (name, timestamp, value, tags_string)

        self._check_duplicate(metric_str)
        if not self._close_client.is_set():
            self._push_metric_to_queue(metric_str)

        return metric_str

    def _validate_metric(self, name, value, tags):
        try:
            assert all(char in self.VALID_METRICS_CHARS for char in name), \
                "Metric name contain incorrect chars '%s'" % name
            assert isinstance(value, (str, int, float)), "Incorrect metric value type '%s'" % type(value)
            assert tags != {}, "Need at least one tag"
        except AssertionError as error:
            raise ValidationError("Metric not valid: %s" % str(error))

    def _check_duplicate(self, metric_str):
        try:
            assert metric_str != self._last_metric
            self._last_metric = metric_str
        except AssertionError:
            if self.raise_duplicate:
                raise MetricDuplicated("Duplicate metric: %s" % metric_str)
            logger.warning("Duplicate metric: %s" % metric_str)

    def _push_metric_to_queue(self, metric_str):
        try:
            self._metrics_queue.put(metric_str, False)
        except queue.Full:
            logger.warning("Drop oldest metric because Queue is full.")
            self._metrics_queue.get()
            self._metrics_queue.put(metric_str, False)

    def __del__(self):
        self.close()
