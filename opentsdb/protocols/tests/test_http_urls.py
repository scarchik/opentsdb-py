
from opentsdb.protocols.http_connect import TSDBUrls, VERSION_ENDPOINT


def test_protocol():
    url = TSDBUrls('127.0.0.1', 4242, protocol='https')
    assert url.version == 'https://127.0.0.1:4242' + VERSION_ENDPOINT


def test_endpoint_prefix():
    url = TSDBUrls('127.0.0.1', 4242, endpoint_prefix='opentsdb')
    assert url.version == 'http://127.0.0.1:4242/opentsdb' + VERSION_ENDPOINT
