"""
The `dispatcher` package provides a structured framework for
registering handlers which are invoked on receipt of websocket
events as required.

Handlers are invoked according to the event type to which they
are mapped. Event types are represented by custom user-defined
status codes. 

Messages sent over websockets by a client to the server are to 
contain an indication of the status code (or event type) 
associated with the message in order for `dispatcher` to
determine what handler(s) to invoke when the message is recieved.

Messages sent by the client must be binary and constructed so
they adhere to the structure outlined below:

1) For textual data:

{HEADER_START}
{
    "{HEADER_KEY}": "some-user-defined-unique-identifier",
    "{HEADER_CODE}": 000,
    "{HEADER_TYPE}": "txt"
}
{HEADER_END}
{
    "some_key": "the content after header_head must be",
    "another_key": "a valid JSON string",
    "key_again": "the user determines what goes inside",
    "last_key": "the JSON string"
}
{BODY_END}

2) For binary data:

{HEADER_START}
{
    "{HEADER_KEY}": "some-user-defined-unique-identifier",
    "{HEADER_CODE}": 000,
    "{HEADER_TYPE}": "bin"
}
{HEADER_END}
b'some raw binary data which may be a document, an image or
even a video file. This is written here with the python
b string syntax only for readability'
{BODY_END}

NOTE:
1) Names enclosed within {} are placeholders. Their values are
   defined in this file.
2) All textual (non-binary) parts of a message must be binary
   encoded.
3) The message structure given above is pretty-printed for 
   readability in this documentation. The actual messages sent
   (or recieved) by a client are compact binary-encoded JSON
   strings (for textual data) or part JSON, part raw binary
   (for binary data).
"""


# magic strings
HEADER_START = '#LHS$'
HEADER_END = '#LHE$'
BODY_END = '#LBE$'

# header structure
HEADER_KEY = 'key'
HEADER_CODE = 'status_code'
HEADER_TYPE = 'data_type'

# data types
DATA_TYPE_TEXT = 'txt'
DATA_TYPE_BINARY = 'bin'

# byte sizes
HEADER_SIZE = 82
MAX_CONTENT_SIZE = 1024 * 1024

# byte values
FILL_VALUE = 32

# auth
AUTH_KEY = 'AUTH_HEADER'