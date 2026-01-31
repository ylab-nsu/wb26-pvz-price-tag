import time

from .config import *

def epd_digital_write(pin, value):
    pin.value(value)

def epd_digital_read(pin):
    return pin.value()

def epd_delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def spi_transfer(data):
    spi.write(bytearray(data))

def epd_init():
    rst.value(0)
    epd_delay_ms(200)
    rst.value(1)
    epd_delay_ms(200)
    return 0

