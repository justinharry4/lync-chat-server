from rest_framework.exceptions import APIException
from rest_framework import status


class ResourceLocked(APIException):
    status_code = status.HTTP_423_LOCKED
    default_detail = 'writes to the resource are not allowed'
    default_code = 'locked'