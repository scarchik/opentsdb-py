from threading import Lock
from functools import wraps
from logging import getLogger
import time

from opentsdb.exceptions import TagsError

logger = getLogger('opentsdb-py')


def send_metric(func):

    def validate_tags(tag_values_length, tag_names_length, optional_tags):
        if optional_tags is False and tag_values_length != tag_names_length:
            raise TagsError("Tags is incorrect, expected %d != %d" % (tag_names_length, tag_values_length))

    @wraps(func)
    def wrapper(self: Metric, *args, **kwargs):
        with self._lock:
            try:
                func(self, *args, **kwargs)
                tags = self.pop_tags()
                validate_tags(len(tags), self.tag_names_length, self.optional_tags)
                return self.client.send(self.name, self._value.get(), **tags)
            except ValueError as error:
                logger.error(error)

    return wrapper


class Metric:

    def __init__(self, name: str, tag_names=(), client=None, optional_tags=False):
        self.name = name

        self.tag_names = tag_names
        self.tag_names_length = len(tag_names)
        self.optional_tags = optional_tags

        self.client = client

        self._value = None
        self._tags = None
        self._lock = Lock()

    @property
    def value(self):
        return self._value.get()

    def tags(self, *tag_values):
        if len(tag_values) > self.tag_names_length:
            raise TagsError("Too many tags is set, expected %d" % self.tag_names_length)

        self._tags = dict(zip(self.tag_names, tag_values))

        return self

    def pop_tags(self) -> dict:
        tags = self._tags or {}
        self._tags = None
        return tags


class _MetricValue:
    def __init__(self):
        self._value = 0.0
        self._lock = Lock()

    def inc(self, amount):
        with self._lock:
            self._value += amount

    def set(self, value):
        with self._lock:
            self._value = value

    def get(self):
        with self._lock:
            return self._value


class Counter(Metric):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = _MetricValue()
        logger.info("Metric registered [type: Counter]: %s", self.name)

    @send_metric
    def inc(self, amount=1):
        if amount < 0:
            raise ValueError('Counters can only be incremented by non-negative amounts.')
        self._value.inc(amount)

    def __str__(self):
        return "%s %s" % (self.name, self._value.get())


class Gauge(Metric):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = _MetricValue()
        logger.info("Metric registered [type: Gauge]: %s", self.name)

    @send_metric
    def inc(self, amount=1):
        self._value.inc(amount)

    @send_metric
    def dec(self, amount=1):
        self._value.inc(-amount)

    @send_metric
    def set(self, value: float):
        self._value.set(float(value))

    def timeit(self, timer=time.perf_counter):
        return _GaugeTimer(self, timer)


class _GaugeTimer:
    def __init__(self, gauge, timer):
        self._gauge = gauge
        self._timer = timer

    def __enter__(self):
        self._start = self._timer()

    def __exit__(self, *_):
        self._gauge.set(max(self._timer() - self._start, 0))

    def __call__(self, func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapped
