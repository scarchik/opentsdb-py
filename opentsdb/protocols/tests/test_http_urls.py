from opentsdb.protocols.http_connect import TSDBUrls


def test_from_host_port():
    url = TSDBUrls.from_host_and_port('127.0.0.1', 4242, version_endpoint="/api/version",
                                      put_endpoint="/api/put?details=true")
    assert url.put == 'http://127.0.0.1:4242/api/put?details=true'


def test_from_uri():
    url = TSDBUrls.from_uri('https://127.0.0.1:4242/opentsdb', version_endpoint="/api/version",
                            put_endpoint="/api/put?details=true")
    assert url.version == 'https://127.0.0.1:4242/opentsdb/api/version'
