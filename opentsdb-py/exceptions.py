

class TSDBClientException(Exception):
    pass


class TagsError(TSDBClientException):
    pass


class MetricDuplicated(TSDBClientException):
    pass


class ValidationError(TSDBClientException):
    pass
