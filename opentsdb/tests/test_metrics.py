from opentsdb import TSDBClient, Counter, Gauge


def test_count(http_client2: TSDBClient):
    http_client2.is_connected()
    http_client2.TEST_METRIC = Counter('test.metric.counter')
    metric = http_client2.TEST_METRIC.inc()
    assert metric['value'] == 1
    metric = http_client2.TEST_METRIC.inc()
    assert metric['value'] == 2


def test_count_with_tag(http_client2: TSDBClient):
    http_client2.is_connected()
    http_client2.TEST_METRIC2 = Counter('test.metric2.counter', ['tag1'])
    metric = http_client2.TEST_METRIC2.tags('tag1').inc()
    assert 'tag1' in metric['tags']


def test_gauge(http_client2: TSDBClient):
    http_client2.is_connected()
    http_client2.TEST_METRIC = Gauge('test.metric.gauge')
    metric = http_client2.TEST_METRIC.inc()
    assert metric['value'] == 1
    metric = http_client2.TEST_METRIC.set(10)
    assert metric['value'] == 10
    metric = http_client2.TEST_METRIC.dec()
    assert metric['value'] == 9
