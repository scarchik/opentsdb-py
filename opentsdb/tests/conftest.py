from os import environ

import pytest

from opentsdb import TSDBClient, TSDBConnectProtocols


@pytest.fixture
def tsdb_host():
    return environ.get('OPEN_TSDB_HOST', '127.0.0.1')


@pytest.fixture
def tsdb_port():
    return int(environ.get('OPEN_TSDB_PORT', '4242'))


@pytest.fixture
def http_client(tsdb_host, tsdb_port):
    return TSDBClient(tsdb_host, tsdb_port, host_tag=False, test_mode=True)


@pytest.fixture
def http_client2(tsdb_host, tsdb_port):
    return TSDBClient(tsdb_host, tsdb_port, host_tag=True, test_mode=True)


@pytest.fixture
def telnet_client(tsdb_host, tsdb_port):
    return TSDBClient(tsdb_host, tsdb_port, protocol=TSDBConnectProtocols.TELNET, host_tag=True, test_mode=True)
