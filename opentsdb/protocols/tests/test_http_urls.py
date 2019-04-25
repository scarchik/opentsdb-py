
from opentsdb.protocols.http_connect import TSDBUrls


def test_from_host_port():
    url = TSDBUrls.from_host_and_port('127.0.0.1', 4242)
    assert url.version == 'http://127.0.0.1:4242' + TSDBUrls.VERSION_ENDPOINT


def test_from_uri():
    url = TSDBUrls.from_uri('https://127.0.0.1:4242/opentsdb')
    assert url.version == 'https://127.0.0.1:4242/opentsdb' + TSDBUrls.VERSION_ENDPOINT
