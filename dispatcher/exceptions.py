class ProtocolError(Exception):
    """
    Base class for all `dispatcher` exceptions.
    """
    pass


class InvalidFrame(ProtocolError):
    """
    Exception raised when a message frame does not conform
    to the structure defined by `dispatcher`'s protocol.
    """
    pass


class UnexpectedJSONInterface(ProtocolError):
    """
    Exception raised when an unexpected key is encountered
    during a parsing operation.
    """
    pass


class InvalidData(ProtocolError):
    """
    Exception raised when a validation error occurs.
    """
    pass


class NotAuthenticated(ProtocolError):
    """
    Exception raised when user authentication is unsuccessful.
    """
    pass


class CodeNotAllowed(ProtocolError):
    """
    Exception raised when a handler attempts handle an event
    with a status code which is not registered with the 
    handler.
    """
    pass