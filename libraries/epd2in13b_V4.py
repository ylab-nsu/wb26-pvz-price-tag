# epd2in13b_V4.py - адаптировано для MicroPython / ESP32
# Оригинал Waveshare 2022, адаптация

from machine import Pin, SPI
from time import sleep_ms

EPD_WIDTH  = 122
EPD_HEIGHT = 250

class EPD:
    def __init__(self, spi, cs_pin, dc_pin, rst_pin, busy_pin):
        self.spi = spi
        self.cs   = cs_pin
        self.dc   = dc_pin
        self.rst  = rst_pin
        self.busy = busy_pin

        # Инициализация пинов
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    def reset(self):
        self.rst(1)
        sleep_ms(20)
        self.rst(0)
        sleep_ms(2)
        self.rst(1)
        sleep_ms(20)

    def send_command(self, command):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)

    def send_data(self, data):
        self.dc(1)
        self.cs(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs(1)

    def busy_wait(self):
        while self.busy.value() != 0:  # 0 = busy (в коде Waveshare: !=0 значит busy)
            sleep_ms(10)

    def init(self):
        self.reset()

        self.busy_wait()
        self.send_command(0x12)  # SWRESET
        self.busy_wait()

        self.send_command(0x01)  # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x03)

        self.set_windows(0, 0, self.width-1, self.height-1)
        self.set_cursor(0, 0)

        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.send_command(0x21)  # Display update control
        self.send_data(0x80)
        self.send_data(0x80)

        self.busy_wait()

    def set_windows(self, xstart, ystart, xend, yend):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((xstart >> 3) & 0xFF)
        self.send_data((xend   >> 3) & 0xFF)

        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(ystart & 0xFF)
        self.send_data((ystart >> 8) & 0xFF)
        self.send_data(yend & 0xFF)
        self.send_data((yend >> 8) & 0xFF)

    def set_cursor(self, xstart, ystart):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(xstart & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(ystart & 0xFF)
        self.send_data((ystart >> 8) & 0xFF)

    def display(self, buffer_black, buffer_red):
        self.send_command(0x24)  # black/white
        self.send_data(buffer_black)

        self.send_command(0x26)  # red
        self.send_data(buffer_red)

        self.send_command(0x20)  # DISPLAY_REFRESH (ondisplay)
        self.busy_wait()

    def clear(self):
        line_width = (self.width + 7) // 8
        buf = bytearray([0xFF] * (line_width * self.height))  # 0xFF = white

        self.send_command(0x24)
        self.send_data(buf)

        self.send_command(0x26)
        self.send_data(buf)

        self.send_command(0x20)
        self.busy_wait()

    def sleep(self):
        self.send_command(0x10)  # DEEP_SLEEP
        self.send_data(0x01)
        sleep_ms(2000)
