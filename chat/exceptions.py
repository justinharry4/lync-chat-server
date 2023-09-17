from rest_framework.exceptions import APIException
from rest_framework import status

from . import status as lync_status


class ResourceLocked(APIException):
    status_code = status.HTTP_423_LOCKED
    default_detail = 'writes to the resource are not allowed'
    default_code = 'locked'



# messaging protocol exceptions

class ProtocolError(Exception):
    status_code = lync_status.SERVER_INTERNAL_ERROR


class InvalidFrame(ProtocolError):
    status_code = lync_status.SERVER_PARSING_ERROR


class UnexpectedJSONInterface(ProtocolError):
    status_code = lync_status.SERVER_UNEXPECTED_INTERFACE


class InvalidMessageData(ProtocolError):
    status_code = lync_status.SERVER_INVALID_DATA


# others
class UnboundDecorator(Exception):
    pass