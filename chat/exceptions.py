from rest_framework.exceptions import APIException
from rest_framework import status

from . import status as lync_status


class ResourceLocked(APIException):
    status_code = status.HTTP_423_LOCKED
    default_detail = 'Retrieval or modification of the resource is not allowed'
    default_code = 'locked'



# messaging protocol exceptions

class ProtocolError(Exception):
    status_code = lync_status.SERVER_INTERNAL_ERROR


class InvalidFrame(ProtocolError):
    status_code = lync_status.SERVER_PARSING_ERROR


class UnexpectedJSONInterface(ProtocolError):
    status_code = lync_status.SERVER_UNEXPECTED_INTERFACE


class InvalidData(ProtocolError):
    status_code = lync_status.SERVER_INVALID_DATA


class NotAuthenticated(ProtocolError):
    status_code = lync_status.SERVER_NOT_AUTHENTICATED


# others
class UnboundDecorator(Exception):
    pass


class CodeNotAllowed(Exception):
    pass