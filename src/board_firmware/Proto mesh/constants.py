class MSG_TYPE:
    DATA = 0x01
    ACK = 0x02
    SET_PRICE = 0x03
    SEND_ID = 0x04
    BYE = 0x05
    PING = 0x06
    PONG = 0x07
    FRAGMENT = 0x10

class MSG_TARGET:
    ALL = 0xFFFF       # Широковещательный
    HUB = 0x0001       # Хаб

class LOG:
    NOTHING = 0
    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4