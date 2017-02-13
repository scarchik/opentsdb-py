

class TSDBClientException(Exception):
    pass


class TSDBConnectionError(TSDBClientException):
    pass


class TagsError(TSDBClientException):
    pass


class MetricDuplicated(TSDBClientException):
    pass


class ValidationError(TSDBClientException):
    pass
