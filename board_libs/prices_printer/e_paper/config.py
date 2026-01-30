from machine import Pin, SPI


EPD_WIDTH = 122
EPD_HEIGHT = 250

RST_PIN = 16
DC_PIN = 17
CS_PIN = 5
BUSY_PIN = 4

SCK_PIN = 18
MOSI_PIN = 23

rst = Pin(RST_PIN, Pin.OUT)
dc = Pin(DC_PIN, Pin.OUT)
cs = Pin(CS_PIN, Pin.OUT)
busy = Pin(BUSY_PIN, Pin.IN)

spi = SPI(2, baudrate=2_000_000, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
