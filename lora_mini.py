# lora_mini.py
import machine
import time
import random

import utils
from constants import LOG

# TODO
# from constants import LoRaConst

class LoRaMini:
    # Константы
    MAX_PACKET_SIZE = 240   # Максимальный размер пакета в байтах
    ACK_TIMEOUT = 2000      # Таймаут ожидания ACK в мс
    AUX_WAIT_TIMEOUT = 1000 # Таймаут готовности по сигналу от AUX в мс
    MSG_READ_TIMEOUT = 100
    
    def __init__(self, config):
        """
        Инициализация LoRa модуля.
        config должен содержать:
        - LORA_M0, LORA_M1, LORA_TX, LORA_RX
        - LORA_UART_NUM, LORA_BAUDRATE
        - NODE_NAME (имя узла)
        """
        self.config = config
        
        # Инициализация пинов режима
        self.m0 = machine.Pin(config.LORA_M0, machine.Pin.OUT)
        self.m1 = machine.Pin(config.LORA_M1, machine.Pin.OUT)
        self.aux = machine.Pin(config.LORA_AUX, machine.Pin.IN)
        
        # Установка нормального режима (0, 0)
        self.set_mode_normal()
        
        # Инициализация UART
        self.uart = machine.UART(
            config.LORA_UART_NUM,
            baudrate=config.LORA_BAUDRATE,
            tx=machine.Pin(config.LORA_TX),
            rx=machine.Pin(config.LORA_RX)
        )
        
        utils.log(f"[LoRaMini] Node {config.NODE_NAME} inited", LOG.INFO)
    
    def set_mode_normal(self):
        """Установка нормального режима (0, 0)"""
        self.m0.value(0)
        self.m1.value(0)
        time.sleep(0.1)  # временный сон, чтобы наверняка
    
    def wait_for_aux(self, timeout_ms=AUX_WAIT_TIMEOUT):
        """
        Ожидание, когда AUX перейдет в HIGH (модуль готов)
        
        Args:
            timeout: максимальное время ожидания в мс
            
        Returns:
            bool: True если модуль готов, False если таймаут
        """
        start = time.ticks_ms()
        
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self.aux.value() == 1:  # AUX HIGH = модуль готов
                return True
            time.sleep_ms(1)
        
        utils.log(f"[WARNING] Timeout wait AUX ({timeout_ms} ms)", LOG.WARN)
        return False
    
    def send_string(self, string):
        """
        Отправляет строку в радиоэфир (в виде байт)

        Args:
            data: данные для отправки (str или bytes)
            target: целевой узел (если None - broadcast)
            need_ack: требуется подтверждение
            msg_type: тип сообщения
        
        Returns:
            int:
            0 - success
            1 - error
            -x (neg int) - count of sent bytes
        """
        # Конвертация в байты
        string_bytes = string.encode('utf-8')
        
        # Проверка размера
        if len(string_bytes) > self.MAX_PACKET_SIZE:
            utils.log(f"[ERROR] Msg is so big: {len(string_bytes)} > {self.MAX_PACKET_SIZE}", LOG.ERROR)
            return 1
        
        # Ожидание готовности модуля перед отправкой
        if not self.wait_for_aux():
            utils.log("[ERROR] Module is not ready for send", LOG.ERROR)
            return 1
        
        # Отправка
        try:
            bytes_written = self.uart.write(string_bytes)
            
            if bytes_written == len(string_bytes):                
                # Добавление в историю
                self.history.add(id)
                
                utils.log(
                    f"[SEND] {len(string_bytes)} bytes: {string}", 
                    level=LOG.INFO
                )
                return 0
            else:
                utils.log(
                    f"[ERROR] Sent not all: {bytes_written}/{len(string_bytes)} bytes",
                    level=LOG.ERROR
                )
                return -bytes_written # not all
            
        except Exception as e:
            utils.log(f"[ERROR] Sending error: {e}", LOG.ERROR)
            return 1
    
    def receive_msg(self, timeout_ms=100):
        """
        Прием сообщения с таймаутом
        
        Returns:
            Строка или None
        """
        start_time = time.ticks_ms()
        last_data_time = start_time
        buffer = b''

        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            if self.uart.any():
                chunk = self.uart.read()
                if chunk:
                    buffer += chunk
                    last_data_time = time.ticks_ms()
            
            # Если прошло N мс без данных - считаем пакет полным
            if buffer and time.ticks_diff(time.ticks_ms(), last_data_time) > 50:
                break
            
            time.sleep_ms(10)
        
        if buffer:
            try:
                # Декодируем байты обратно в строку UTF-8
                return buffer.decode('utf-8')
            except UnicodeDecodeError:
                utils.log("[ERROR] lora.receive_msg(): can't decode", LOG.ERROR)
        
        return None