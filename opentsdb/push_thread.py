from logging import getLogger
from queue import Empty
import threading
import random
import time

from opentsdb.exceptions import TSDBConnectionError

logger = getLogger('opentsdb-py')


class PushThread(threading.Thread):

    def __init__(self, tsdb_connect, metrics_queue, close_client, send_metrics_limit, test_mode):
        super().__init__()
        self.tsdb_connect = tsdb_connect
        self.metrics_queue = metrics_queue
        self.close_client_flag = close_client
        self.send_metrics_limit = send_metrics_limit
        self.test_mode = test_mode

        self.retry_send_metric = None

    def run(self):
        while not self._is_done():
            start_time = time.time()

            try:
                metric = self._next_metric()
            except Empty:
                continue

            logger.debug("Send metric: %s", metric)
            if not self.test_mode:
                try:
                    self.tsdb_connect.sendall(metric.encode('utf-8'))
                except TSDBConnectionError:
                    self.retry_send_metric = metric
                    time.sleep(0.5)
                except Exception as error:
                    logger.exception("Push metric failed: %s", error)
                    self.retry_send_metric = metric
                    time.sleep(1)

            self.__metrics_limit_timeout(start_time)

        self.tsdb_connect.disconnect()

    def _is_done(self):
        return self.tsdb_connect.stopped.is_set() or (self.close_client_flag.is_set() and self.metrics_queue.empty())

    def _next_metric(self, wait_timeout=3):
        if self.retry_send_metric:
            metric = self.retry_send_metric
            self.retry_send_metric = None
        else:
            metric = self.metrics_queue.get(block=True, timeout=wait_timeout)

        return metric

    def __metrics_limit_timeout(self, start_time):
        duration = time.time() - start_time
        if self.send_metrics_limit > 0:
            wait_time = (2.0 * random.random()) / self.send_metrics_limit
            if wait_time > duration:
                logger.debug("Wait for %s", wait_time - duration)
                time.sleep(wait_time - duration)
