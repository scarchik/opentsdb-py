# opentsdb-py
Python client for OpenTSDB

## Installation
```bash
pip3 install git+https://github.com/orionvm/potsdb.git
```

## Usage
```python
from opentsdb import TSDBClient, Counter, Gauge

tsdb = TSDBClient('opentsdb.domain', port=4242, static_tags={'node': 'ua.node.12'})

tsdb.USERS_COUNT = Counter('users.count', ['group'])
tsdb.ACTIVE_USERS = Gauge('users.active')

tsdb.USERS_COUNT.tags('guest').inc()
tsdb.USERS_COUNT.tags('guest').inc()
tsdb.USERS_COUNT.tags('guest').inc(14)

tsdb.ACTIVE_USERS.inc()
tsdb.ACTIVE_USERS.dec()
tsdb.ACTIVE_USERS.set(12)

```