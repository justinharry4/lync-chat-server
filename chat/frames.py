import json

from . import protocol
from .exceptions import InvalidFrame, UnexpectedJSONInterface


MAGIC_STR_LENGTH = len(protocol.HEADER_START)

START_STR_POS = 0
SEP_STR_POS = MAGIC_STR_LENGTH + protocol.HEADER_SIZE
END_STR_POS = -MAGIC_STR_LENGTH


class FrameParser():
    def __init__(self, message):
        self.raw_message = message

    def validate_magic_strings(self):
        start_str_end = START_STR_POS + MAGIC_STR_LENGTH
        start_bytes = self.raw_message[START_STR_POS:start_str_end]
        start_str = start_bytes.decode()

        sep_str_end = SEP_STR_POS + MAGIC_STR_LENGTH
        sep_bytes = self.raw_message[SEP_STR_POS:sep_str_end]
        sep_str = sep_bytes.decode()
    
        end_bytes = self.raw_message[END_STR_POS:]
        end_str = end_bytes.decode()

        if start_str != protocol.HEADER_START:
            raise InvalidFrame(
                f'Invalid header start string `{start_str}`'
            )
        if sep_str != protocol.HEADER_END:
            raise InvalidFrame(
                f'Invalid header end string `{sep_str}`'
            )
        if end_str != protocol.BODY_END:
            raise InvalidFrame(
                f'Invalid body end string `{end_str}`'
            )

    def get_header(self):
        header_start = START_STR_POS + MAGIC_STR_LENGTH
        header_end = SEP_STR_POS

        header_bytes = self.raw_message[header_start:header_end]
        
        try:
            header = json.loads(header_bytes)
        except json.JSONDecodeError as exc:
            raise InvalidFrame(
                'header string is not valid JSON'
            ) from exc

        allowed_header_keys = [
            protocol.HEADER_KEY,
            protocol.HEADER_CODE,
            protocol.HEADER_TYPE
        ]

        for key in header:
            if key not in allowed_header_keys:
                raise UnexpectedJSONInterface(
                    f'invalid key `{key}` in header'
                )
        
        return header
    
    def get_body(self, data_type):
        body_start = SEP_STR_POS + MAGIC_STR_LENGTH
        body_end = END_STR_POS

        body_bytes = self.raw_message[body_start:body_end]

        if data_type == protocol.DATA_TYPE_TEXT:
            try:
                body = json.loads(body_bytes)
            except json.JSONDecodeError as exc:
                raise InvalidFrame(
                    'body string is not valid JSON'
                ) from exc
        elif data_type == protocol.DATA_TYPE_BINARY:
            body = body_bytes
        
        return body
    
    def parse(self):
        self.validate_magic_strings()

        header = self.get_header()
        data_type = header[protocol.HEADER_TYPE]
        body = self.get_body(data_type)

        message = {'header': header, 'body': body}

        return message
        

class TextFrame():
    def __init__(self, key, code, data={}):
        self.key = key
        self.code = code
        self.body_data = data

        self.generate_frame()

    def generate_frame(self):
        enc = 'utf-8'

        start_bytes = bytes(protocol.HEADER_START, enc)
        sep_bytes =  bytes(protocol.HEADER_END, enc)
        end_bytes = bytes(protocol.BODY_END, enc)

        header_dict = {
            protocol.HEADER_KEY: self.key,
            protocol.HEADER_CODE: self.code,
            protocol.HEADER_TYPE: protocol.DATA_TYPE_TEXT
        }
        header_str = json.dumps(header_dict, separators=(',',':'))
        header_bytes = bytes(header_str, enc)

        body_dict = self.body_data
        body_str = json.dumps(body_dict, separators=(',',':'))
        body_bytes = bytes(body_str, enc)
        
        parts = [
            start_bytes,
            header_bytes,
            sep_bytes,
            body_bytes,
            end_bytes
        ]

        frame = bytearray()
        for part in parts:
            frame.extend(part)

        self.data = bytes(frame)