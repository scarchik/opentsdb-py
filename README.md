# opentsdb-py
Python client for OpenTSDB

## Installation

Install
```bash
pip3 install opentsdb-py
```

Install latest version from Git:
```bash
pip3 install git+https://github.com/scarchik/opentsdb-py.git
```

## Usage

```python
import logging

from opentsdb import TSDBClient, Counter, Gauge

logging.basicConfig(level=logging.DEBUG)

tsdb = TSDBClient('opentsdb.address', static_tags={'node': 'ua.node.12'})

tsdb.USERS_COUNT = Counter('users.count')
tsdb.ACTIVE_USERS = Gauge('users.active')

tsdb.USERS_COUNT.inc()
tsdb.USERS_COUNT.inc(4)

tsdb.ACTIVE_USERS.inc()
tsdb.ACTIVE_USERS.inc()
tsdb.ACTIVE_USERS.dec()
tsdb.ACTIVE_USERS.set(12)

tsdb.close()
tsdb.wait()
```

Example output:
```
INFO:opentsdb-py:Metric registered [type: Counter]: users.count
INFO:opentsdb-py:Metric registered [type: Gauge]: users.active
DEBUG:opentsdb-py:Connect to OpenTSDB: opentsdb.address:4242
DEBUG:opentsdb-py:Send metric: put users.count 1482918649 1.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Send metric: put users.count 1482918649 5.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Wait for 0.00036912765390552285
DEBUG:opentsdb-py:Send metric: put users.active 1482918649 1.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Wait for 0.0015149837935762014
DEBUG:opentsdb-py:Send metric: put users.active 1482918649 2.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Wait for 0.001194864658922911
DEBUG:opentsdb-py:Send metric: put users.active 1482918649 1.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Wait for 0.0017368242784542947
DEBUG:opentsdb-py:Send metric: put users.active 1482918649 12.0 node=ua.node.12 host=pc4299
DEBUG:opentsdb-py:Wait for 0.0011665662644835626
DEBUG:opentsdb-py:Disconnecting from opentsdb.address:4242
```

Module provide two ways to send metrics, first like shown on example above.
Second, simple use method .send()

```python
from opentsdb import TSDBClient

tsdb = TSDBClient('opentsdb.address', static_tags={'node': 'ua.node.12'})

tsdb.send('metric.test', 1, tag1=val1, tag2=val2)

tsdb.close()
tsdb.wait()
```


## TSDBClient arguments
 * **host** - default: environ.get('OPEN_TSDB_HOST', '127.0.0.1')
 * **port** - default: environ.get('OPEN_TSDB_PORT', 4242)
 * **check_tsdb_alive** - (default: False) on start client will check is OpenTSDB alive and if not raise exception. 
 * **static_tags** - (default: None) specify tags which will add for each metric.
 * **host_tag** - (default: True) add tag host to metric
 * **raise_duplicate** - (default: True) raise MetricDuplicated exception when metric duplicated
 * **test_mode** - (default: False) don't send metric to OpenTSDB server
 * **max_queue_size** - (default: 10000) max size of queue for metrics
 * **send_metrics_limit** - (default: 1000) send metrics per second limit

## Instruments

Module provide two type metrics: Counter, Gauge

### Counter
Counter can only go up, and reset when the process restarts.

```python
from opentsdb import TSDBClient, Counter

tsdb = TSDBClient('opentsdb.address')

tsdb.USERS_COUNT = Counter('users.count') # recommended way to specify metric

my_metric = Counter('users.count', client=tsdb) # alternative way

tsdb.USERS_COUNT.inc()
tsdb.USERS_COUNT.inc(4) # amount can be changed, default 1
tsdb.wait()
```

### Gauge
Gauges can go up and down.

```python
from opentsdb import TSDBClient, Gauge

tsdb = TSDBClient('opentsdb.address')

tsdb.ACTIVE = Gauge('metric.active')

tsdb.ACTIVE.inc()
tsdb.ACTIVE.dec()
tsdb.ACTIVE.set(17)
tsdb.wait()
```

### Tags
OpenTSDB allow tags to each metric, and minimum it one, and max recommended = 8.

```python
from opentsdb import TSDBClient, Counter

tsdb = TSDBClient('opentsdb.address')

tsdb.REQUEST_TOTAL = Counter('request.total', ['method', 'endpoint', 'status'])

tsdb.REQUEST_TOTAL.tags('get', '/users', 200).inc()

# Enable optional tags
tsdb.REQUEST_TOTAL = Counter('request.total', ['method', 'endpoint', 'status'], optional_tags=True)

tsdb.REQUEST_TOTAL.tags('get', '/users').inc()  # if you not specify last tag, it will work
tsdb.REQUEST_TOTAL.tags('get').inc()  # and thats one will work too

tsdb.wait()
```


## Exceptions

### TSDBClientException
opentsdb-py global exception

### TagsError
Raise when tags not specified or specified more than provide

### MetricDuplicated
Raise when try to send the same as previous metric

### ValidationError
Raise when metric not valid

    * metric contain incorrect chars, valid only: string.ascii_letters + string.digits + '-_./'
    * metric value type incorrect, valid only: str, int, float
    * tags not specified, at least one tag is required

