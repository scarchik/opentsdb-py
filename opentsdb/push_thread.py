from logging import getLogger
from queue import Empty
import threading
import random
import time

logger = getLogger('opentsdb-py')


class PushThread(threading.Thread):

    WAIT_NEXT_METRIC_TIMEOUT = 3

    def __init__(self, tsdb_connect, metrics_queue, close_client,
                 send_metrics_limit, send_metrics_batch_limit, test_mode):
        super().__init__()
        self.tsdb_connect = tsdb_connect
        self.metrics_queue = metrics_queue
        self.close_client_flag = close_client
        self.send_metrics_limit = send_metrics_limit
        self.send_metrics_batch_limit = send_metrics_batch_limit
        self.test_mode = test_mode

        self._retry_send_metrics = None

    def run(self):
        while not self._is_done():
            start_time = time.time()

            try:
                if self._retry_send_metrics:
                    data = self._retry_send_metrics
                    self._retry_send_metrics = None
                else:
                    data = self._next(self.WAIT_NEXT_METRIC_TIMEOUT)
            except StopIteration:
                break
            except Empty:
                continue

            if not self.test_mode:
                self.send(data)

            if self.send_metrics_limit > 0:
                self.__metrics_limit_timeout(start_time)

        self.tsdb_connect.disconnect()

    def _is_done(self):
        return self.tsdb_connect.stopped.is_set() or (self.close_client_flag.is_set() and self.metrics_queue.empty())

    def _next(self, wait_timeout):
        raise NotImplementedError()

    def send(self, data):
        raise NotImplementedError()

    def __metrics_limit_timeout(self, start_time):
        pass


class HTTPPushThread(PushThread):

    def _next(self, wait_timeout):
        total_metrics = self.metrics_queue.qsize()
        iter_count = total_metrics if total_metrics <= self.send_metrics_batch_limit else self.send_metrics_batch_limit
        metrics = []
        if total_metrics:
            for _ in range(iter_count):
                metrics.append(self.metrics_queue.get_nowait())
        else:
            metrics.append(self.metrics_queue.get(block=True, timeout=wait_timeout))

        if StopIteration in metrics and len(metrics) == 1:
            raise StopIteration
        elif StopIteration in metrics:
            metrics.remove(StopIteration)
            self.metrics_queue.put(StopIteration)
        return metrics

    def send(self, data):
        try:
            result = self.tsdb_connect.sendall(*data)
        except Exception as error:
            logger.exception("Push metric failed: %s", error)
            self._retry_send_metrics = data
            time.sleep(1)
        else:
            if result.get('failed') > 0:
                logger.warning(
                    "Push metric from batch failed %d/%d." % result.get('failed'), len(data),
                    extra=result.get('errors'))


class TelnetPushThread(PushThread):

    def _next(self, wait_timeout):
        metric = self.metrics_queue.get(block=True, timeout=wait_timeout)

        if metric is StopIteration:
            raise metric
        return metric

    def __metrics_limit_timeout(self, start_time):
        duration = time.time() - start_time
        wait_time = (2.0 * random.random()) / self.send_metrics_limit
        if wait_time > duration:
            logger.debug("Wait for %s", wait_time - duration)
            time.sleep(wait_time - duration)

    def send(self, data):
        try:
            self.tsdb_connect.sendall(data)
        except Exception as error:
            logger.exception("Push metric failed: %s", error)
            self._retry_send_metrics = data
            time.sleep(1)
