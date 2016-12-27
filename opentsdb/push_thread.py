from logging import getLogger
from queue import Empty
import threading
import random
import time

logger = getLogger('opentsdb-py')


class PushThread(threading.Thread):
    SEND_METRICS_PER_SECOND_LIMIT = 1000

    def __init__(self, tsdb_connect, metrics_queue, close_client, test_mode):
        super().__init__()
        self.tsdb_connect = tsdb_connect
        self.metrics_queue = metrics_queue
        self.close_client_flag = close_client
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
                except Exception as error:
                    logger.error("Push metric failed: %s", error)
                    self.retry_send_metric = metric
                    time.sleep(1)
                    continue

            self.__metrics_limit_timeout(start_time)

        self.tsdb_connect.disconnect()

    def _is_done(self):
        return self.tsdb_connect.stopped.is_set() or (self.close_client_flag.is_set() and self.metrics_queue.empty())

    def _next_metric(self):
        if self.retry_send_metric:
            metric = self.retry_send_metric
            self.retry_send_metric = None
        else:
            metric = self.metrics_queue.get(block=True, timeout=3)

        return metric

    def __metrics_limit_timeout(self, start_time):
        duration = time.time() - start_time
        if self.SEND_METRICS_PER_SECOND_LIMIT > 0:
            wait_time = (2.0 * random.random()) / self.SEND_METRICS_PER_SECOND_LIMIT
            if wait_time > duration:
                logger.debug("Wait for %s", wait_time - duration)
                time.sleep(wait_time - duration)
