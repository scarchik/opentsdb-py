import time

import pytest

from opentsdb.tsdb_client import TSDBClient, TSDBConnectProtocols
from opentsdb.exceptions import ValidationError, TSDBNotAlive

MAX_STOP_DURATION = 1  # seconds


def test_no_tag_send(http_client: TSDBClient):
    pytest.raises(ValidationError, http_client.send, 'test', 1)


def test_bad_value_send(http_client: TSDBClient):
    pytest.raises(ValidationError, http_client.send, 'test', b'')
    pytest.raises(ValidationError, http_client.send, 'test', [])
    pytest.raises(ValidationError, http_client.send, 'test', {})


def test_bad_chars_send(http_client: TSDBClient):
    pytest.raises(ValidationError, http_client.send, '%test%', 1)


def test_host_tag(telnet_client: TSDBClient):
    metric = telnet_client.send('test', 1)
    assert 'host' in metric['tags']


def test_check_tsdb_alive():
    pytest.raises(
        TSDBNotAlive,
        TSDBClient, '127.0.0.2', 42424, protocol=TSDBConnectProtocols.TELNET, check_tsdb_alive=True)


def test_http_client_close(http_client: TSDBClient):
    start = time.time()
    assert http_client.is_connected()
    http_client.close()
    http_client.wait()
    assert http_client.is_connected() is False
    assert time.time() - start < MAX_STOP_DURATION


def test_telnet_client_close(telnet_client: TSDBClient):
    start = time.time()
    assert telnet_client.is_connected()
    telnet_client.close()
    telnet_client.wait()
    assert telnet_client.is_connected() is False
    assert time.time() - start < MAX_STOP_DURATION


def test_send_metric_through_http(http_client: TSDBClient):
    _test_sending_metric(http_client)


def test_send_metric_through_telnet(telnet_client: TSDBClient):
    _test_sending_metric(telnet_client)


def _test_sending_metric(client: TSDBClient):
    client.send('test', 1, tag1=1)
    assert client.queue_size() == 1
    client.close()
    client.wait()
    assert client.queue_size() == 0
    assert client.statuses['success'] == 1


def test_predefined_metrics(http_client3: TSDBClient):
    assert http_client3.PREDEFINED_METRIC.client is not None
