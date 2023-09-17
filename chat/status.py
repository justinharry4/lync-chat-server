"""Lync custom messaging protocol status codes"""

# no error server codes 
SERVER_HEAD_TEXT_EOC = 601
SERVER_HEAD_TEXT_MCE = 611
SERVER_MORE_TEXT_EOC = 602
SERVER_MORE_TEXT_MCE = 612
SERVER_FILE_DATA = 623
SERVER_ACKNOWLEDGMENT = 624
SERVER_MESSAGE_STATUS = 625
SERVER_MESSAGE_REQUEST = 626

# error server codes
SERVER_UNKNOWN_KEY = 821
SERVER_PARSING_ERROR = 822
SERVER_UNEXPECTED_INTERFACE = 823
SERVER_FILE_ERROR = 824
SERVER_INTERNAL_ERROR = 825
SERVER_INVALID_DATA = 826

# no error client codes
CLIENT_HEAD_TEXT_EOC = 701
CLIENT_HEAD_TEXT_MCE = 711
CLIENT_MORE_TEXT_EOC = 702
CLIENT_MORE_TEXT_MCE = 712
CLIENT_FILE_METADATA = 723
CLIENT_HEAD_FILE_EOC = 704
CLIENT_HEAD_FILE_MCE = 714
CLIENT_MORE_FILE_EOC = 705
CLIENT_MORE_FILE_MCE = 715
CLIENT_ACKNOWLEDGMENT = 726
CLIENT_MESSAGE_STATUS = 727

# error client codes
CLIENT_UNKNOWN_KEY = 921
CLIENT_PARSING_ERROR = 822
CLIENT_UNEXPECTED_INTERFACE = 923
