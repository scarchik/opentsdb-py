

class TSDBClientException(Exception):
    pass


class TagsError(TSDBClientException):
    pass


class MetricDuplicated(TSDBClientException):
    pass


class ValidationError(TSDBClientException):
    pass


class UnknownTSDBConnectProtocol(TSDBClientException):
    def __init__(self, protocol):
        self.protocol = protocol

    def __str__(self):
        return "Unknown TSDB connection protocol: %s" % self.protocol
