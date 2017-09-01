from opentsdb.protocols.http_connect import HttpTSDBConnect
from opentsdb.protocols.telnet_connect import TelnetTSDBConnect
from opentsdb.push_thread import HTTPPushThread, TelnetPushThread
from opentsdb.exceptions import UnknownTSDBConnectProtocol

__all__ = ['HttpTSDBConnect', 'TelnetTSDBConnect', 'TSDBConnectProtocols']


class TSDBConnectProtocols:
    HTTP = 'HTTP'
    TELNET = 'TELNET'

    @classmethod
    def get_connect(cls, protocol: str, *args, **kwargs):
        if protocol == cls.HTTP:
            return HttpTSDBConnect(*args, **kwargs)
        elif protocol == cls.TELNET:
            return TelnetTSDBConnect(*args, **kwargs)
        raise UnknownTSDBConnectProtocol(protocol)

    @classmethod
    def get_push_thread(cls, protocol, *args, **kwargs):
        if protocol == cls.HTTP:
            return HTTPPushThread(*args, **kwargs)
        elif protocol == cls.TELNET:
            return TelnetPushThread(*args, **kwargs)
        raise UnknownTSDBConnectProtocol(protocol)
