class MSG_FIELD:
    ID =        0
    FROM =      1
    TO =        2
    TYPE =      3
    DATA =      4
    TIMESTAMP = 5
    NEED_ACK =  6

class MSG_TYPE:
    DATA = 1
    ACK = 2
    SET_PRICE = 3
    SEND_ID = 4

class MSG_TARGET:
    HUB = "HUB"
    ALL = "ALL"

class LOG:
    NOTHING = 0
    ERROR = 1
    WARN = 2
    INFO = 3
    
