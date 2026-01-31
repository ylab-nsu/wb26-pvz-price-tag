"""
lora_mesh.py
LoRa Mesh протокол с фрагментацией, ACK и ретрансляцией
"""

import machine
import time
import random

from constants import MSG_TYPE, MSG_TARGET, LOG
from config_common import RANDOM_MIN_INT, RANDOM_MAX_INT

# =============================================================================
# ЛОГИРОВАНИЕ
# =============================================================================

_log_level = LOG.INFO

def set_log_level(level):
    global _log_level
    _log_level = level

def log(msg, level=LOG.INFO):
    if level <= _log_level:
        prefixes = {
            LOG.NOTHING: "",
            LOG.ERROR: "ERR",
            LOG.WARN: "WRN",
            LOG.INFO: "INF",
            LOG.DEBUG: "DBG"
        }
        prefix = prefixes.get(level, "")
        print(f"[{prefix}] {msg}")


# =============================================================================
# ЗАГОЛОВОК ПАКЕТА (18 байт)
# =============================================================================
#
# Байт    | Назначение
# --------|------------------------------------------
# 0       | Флаги (бит 7: need_ack, бит 6: is_mesh, биты 0-5: msg_type)
# 1-3     | msg_id (3 байта)
# 4       | fragment_num (номер фрагмента, с 0)
# 5       | fragment_total (всего фрагментов)
# 6-7     | origin_node (изначальный отправитель)
# 8-9     | from_node (последний ретранслятор)
# 10-11   | to_node (конечный получатель)
# 12      | hop_count (сколько прыжков сделано)
# 13      | max_hops (максимум прыжков, TTL)
# 14-17   | timestamp (4 байта, UNIX time)
# 18-57   | data (40 байт)
#

class MeshHeader:
    """Заголовок mesh-пакета (18 байт)"""
    
    SIZE = 18
    DATA_SIZE = 40              # 58 - 18 = 40 байт на данные
    MAX_PACKET_SIZE = 58
    DEFAULT_MAX_HOPS = 5
    
    def __init__(self, msg_type=MSG_TYPE.DATA, msg_id=None,
                 fragment_num=0, fragment_total=1,
                 origin_node=0, from_node=0, to_node=MSG_TARGET.ALL,
                 hop_count=0, max_hops=None,
                 need_ack=False, is_mesh=True, timestamp=None):
        
        self.msg_type = int(msg_type) & 0x3F
        self.msg_id = int(msg_id) if msg_id is not None else random.randint(RANDOM_MIN_INT, RANDOM_MAX_INT)
        self.fragment_num = int(fragment_num) & 0xFF
        self.fragment_total = int(fragment_total) & 0xFF
        self.origin_node = int(origin_node) & 0xFFFF
        self.from_node = int(from_node) & 0xFFFF
        self.to_node = int(to_node) & 0xFFFF
        self.hop_count = int(hop_count) & 0xFF
        self.max_hops = int(max_hops) if max_hops is not None else self.DEFAULT_MAX_HOPS
        self.need_ack = bool(need_ack)
        self.is_mesh = bool(is_mesh)
        self.timestamp = int(timestamp) if timestamp is not None else int(time.time())
    
    def to_bytes(self):
        """Сериализация в 18 байт"""
        header = bytearray(self.SIZE)
        
        # Байт 0: флаги
        flags = self.msg_type & 0x3F
        if self.is_mesh:
            flags |= 0x40
        if self.need_ack:
            flags |= 0x80
        header[0] = flags
        
        # Байты 1-3: msg_id
        msg_id = self.msg_id & 0xFFFFFF
        header[1] = (msg_id >> 16) & 0xFF
        header[2] = (msg_id >> 8) & 0xFF
        header[3] = msg_id & 0xFF
        
        # Байт 4-5: fragment
        header[4] = self.fragment_num & 0xFF
        header[5] = self.fragment_total & 0xFF
        
        # Байты 6-7: origin_node
        header[6] = (self.origin_node >> 8) & 0xFF
        header[7] = self.origin_node & 0xFF
        
        # Байты 8-9: from_node
        header[8] = (self.from_node >> 8) & 0xFF
        header[9] = self.from_node & 0xFF
        
        # Байты 10-11: to_node
        header[10] = (self.to_node >> 8) & 0xFF
        header[11] = self.to_node & 0xFF
        
        # Байт 12-13: hop_count, max_hops
        header[12] = self.hop_count & 0xFF
        header[13] = self.max_hops & 0xFF
        
        # Байты 14-17: timestamp
        ts = self.timestamp & 0xFFFFFFFF
        header[14] = (ts >> 24) & 0xFF
        header[15] = (ts >> 16) & 0xFF
        header[16] = (ts >> 8) & 0xFF
        header[17] = ts & 0xFF
        
        return bytes(header)
    
    @classmethod
    def from_bytes(cls, data):
        """Десериализация из байтов"""
        if len(data) < cls.SIZE:
            raise ValueError(f"Header too small: {len(data)} < {cls.SIZE}")
        
        flags = data[0]
        msg_type = flags & 0x3F
        is_mesh = bool(flags & 0x40)
        need_ack = bool(flags & 0x80)
        
        msg_id = (data[1] << 16) | (data[2] << 8) | data[3]
        fragment_num = data[4]
        fragment_total = data[5]
        origin_node = (data[6] << 8) | data[7]
        from_node = (data[8] << 8) | data[9]
        to_node = (data[10] << 8) | data[11]
        hop_count = data[12]
        max_hops = data[13]
        timestamp = (data[14] << 24) | (data[15] << 16) | (data[16] << 8) | data[17]
        
        return cls(
            msg_type=msg_type, msg_id=msg_id,
            fragment_num=fragment_num, fragment_total=fragment_total,
            origin_node=origin_node, from_node=from_node, to_node=to_node,
            hop_count=hop_count, max_hops=max_hops,
            need_ack=need_ack, is_mesh=is_mesh, timestamp=timestamp
        )
    
    def can_relay(self):
        """Можно ли ретранслировать?"""
        return self.is_mesh and self.hop_count < self.max_hops
    
    def __repr__(self):
        return (f"Hdr(t={self.msg_type},id=0x{self.msg_id:06X},"
                f"f={self.fragment_num}/{self.fragment_total},"
                f"o={self.origin_node},to={self.to_node})")


# =============================================================================
# ПАКЕТ
# =============================================================================

class MeshPacket:
    """Mesh-пакет: заголовок + данные"""
    
    def __init__(self, header, data=b''):
        self.header = header
        self.data = bytes(data[:MeshHeader.DATA_SIZE])
    
    def to_bytes(self):
        packet = bytearray(MeshHeader.MAX_PACKET_SIZE)
        header_bytes = self.header.to_bytes()
        packet[:MeshHeader.SIZE] = header_bytes
        packet[MeshHeader.SIZE:MeshHeader.SIZE + len(self.data)] = self.data
        return bytes(packet)
    
    @classmethod
    def from_bytes(cls, raw):
        if len(raw) < MeshHeader.SIZE:
            raise ValueError(f"Packet too small: {len(raw)}")
        header = MeshHeader.from_bytes(raw[:MeshHeader.SIZE])
        data = bytes(raw[MeshHeader.SIZE:])
        return cls(header, data)
    
    def __repr__(self):
        return f"Packet({self.header}, data={len(self.data)}B)"


# =============================================================================
# TRANSCEIVER (низкоуровневая работа с UART)
# =============================================================================

class LoRaTransceiver:
    """Низкоуровневая работа с LoRa модулем E32"""
    
    AUX_TIMEOUT_MS = 1000
    READ_TIMEOUT_MS = 500
    PACKET_GAP_MS = 50  # Пауза между чтениями для определения конца пакета
    
    def __init__(self, config):
        self.node_id = int(config.NODE_ID)
        
        # Пины управления
        self.m0 = machine.Pin(config.LORA_M0, machine.Pin.OUT)
        self.m1 = machine.Pin(config.LORA_M1, machine.Pin.OUT)
        self.aux = machine.Pin(config.LORA_AUX, machine.Pin.IN)
        
        # Нормальный режим (M0=0, M1=0)
        self.m0.value(0)
        self.m1.value(0)
        time.sleep_ms(100)
        
        # UART
        self.uart = machine.UART(
            config.LORA_UART_NUM,
            baudrate=config.LORA_BAUDRATE,
            tx=machine.Pin(config.LORA_TX),
            rx=machine.Pin(config.LORA_RX)
        )
        
        log(f"LoRa init, node={self.node_id}", LOG.INFO)
    
    def wait_aux(self, timeout_ms=None):
        """Ожидание готовности модуля (AUX=HIGH)"""
        timeout_ms = timeout_ms or self.AUX_TIMEOUT_MS
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self.aux.value() == 1:
                return True
            time.sleep_ms(1)
        log("AUX timeout", LOG.WARN)
        return False
    
    def send_raw(self, data):
        """Отправка сырых байтов"""
        if not self.wait_aux():
            return False
        try:
            written = self.uart.write(data)
            return written == len(data)
        except Exception as e:
            log(f"TX error: {e}", LOG.ERROR)
            return False
    
    def receive_raw(self, timeout_ms=None):
        """Прием сырых байтов"""
        timeout_ms = timeout_ms or self.READ_TIMEOUT_MS
        start = time.ticks_ms()
        last_data = start
        buffer = b''
        
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self.uart.any():
                chunk = self.uart.read()
                if chunk:
                    buffer += chunk
                    last_data = time.ticks_ms()
            
            # Если данные были и пауза > PACKET_GAP_MS — пакет завершен
            if buffer and time.ticks_diff(time.ticks_ms(), last_data) > self.PACKET_GAP_MS:
                break
            
            time.sleep_ms(5)
        
        return buffer if buffer else None
    
    def available(self):
        """Есть ли данные в буфере?"""
        return self.uart.any() > 0
    
    def clear_buffer(self):
        """Очистка буфера UART"""
        while self.uart.any():
            self.uart.read()


# =============================================================================
# MESH NODE (главный класс)
# =============================================================================

class MeshNode:
    """
    LoRa Mesh Node с поддержкой:
    - Автоматической ретрансляции
    - Фрагментации больших сообщений
    - ACK подтверждений
    - Защиты от дубликатов и петель
    """
    # Лимиты для защиты от утечек памяти
    MAX_SEEN_MESSAGES = 100
    MAX_ASSEMBLY_BUFFERS = 10
    MAX_PENDING_ACKS = 20
    MAX_COMPLETED_MESSAGES = 10
    
    def __init__(self, config):
        """
        Args:
            config: объект с атрибутами NODE_ID, LORA_*, MAX_HOPS, RELAY_ENABLED, etc.
        """
        self.node_id = int(config.NODE_ID)
        self.relay_enabled = getattr(config, 'RELAY_ENABLED', True)
        self.max_hops = getattr(config, 'MAX_HOPS', 5)
        
        # Transceiver
        self.lora = LoRaTransceiver(config)
        
        # Буферы
        self.seen_messages = {}       # {msg_id: timestamp} — защита от дубликатов
        self.assembly_buffers = {}    # Сборка фрагментов
        self.completed_messages = []  # Готовые сообщения
        self.pending_acks = {}        # Ожидание ACK: {msg_id: (timestamp, retries, data)}
        
        # Таймауты
        self.seen_ttl_ms = getattr(config, 'SEEN_TTL_MS', 60000)
        self.assembly_ttl_ms = getattr(config, 'ASSEMBLY_TTL_MS', 30000)
        self.ack_timeout_ms = getattr(config, 'ACK_TIMEOUT_MS', 3000)
        self.max_retries = getattr(config, 'MAX_SEND_RETRIES', 3)
        
        # Задержка ретрансляции (случайная, для избежания коллизий)
        self.relay_delay_min_ms = 30
        self.relay_delay_max_ms = 100
        
        # Статистика
        self.stats = {
            'tx': 0,
            'rx': 0,
            'relayed': 0,
            'acks_sent': 0,
            'acks_received': 0,
            'dropped_duplicate': 0,
            'dropped_ttl': 0,
            'timeouts': 0
        }
        
        set_log_level(getattr(config, 'LOG_LEVEL', LOG.INFO))
        log(f"MeshNode init, id={self.node_id}", LOG.INFO)
    
    # -------------------------------------------------------------------------
    # ОТПРАВКА
    # -------------------------------------------------------------------------
    
    def send(self, data, to_node=MSG_TARGET.ALL, msg_type=MSG_TYPE.DATA,
             need_ack=False, delay_ms=100):
        """
        Отправить сообщение (с автоматической фрагментацией).
        
        Args:
            data: str или bytes
            to_node: ID получателя (int или MSG_TARGET)
            msg_type: тип сообщения
            need_ack: требуется подтверждение
            delay_ms: задержка между фрагментами
        
        Returns:
            msg_id (int) или None при ошибке
        """
        # Конвертируем данные
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = bytes(data)
        
        # Конвертируем to_node
        to_node = int(to_node) & 0xFFFF
        
        total_len = len(data_bytes)
        frag_total = max(1, (total_len + MeshHeader.DATA_SIZE - 1) // MeshHeader.DATA_SIZE)
        
        if frag_total > 255:
            log("Message too big", LOG.ERROR)
            return None
        
        msg_id = random.randint(0, 0xFFFFFF)
        timestamp = int(time.time())
        
        log(f"TX: 0x{msg_id:06X}, {total_len}B, {frag_total} frags, to={to_node}", LOG.INFO)
        
        # Отправляем фрагменты
        ffor frag_num in range(frag_total):
            start = frag_num * MeshHeader.DATA_SIZE
            end = min(start + MeshHeader.DATA_SIZE, total_len)
            chunk = data_bytes[start:end]
            
            # Тип: FRAGMENT если много частей, иначе оригинальный тип
            actual_type = MSG_TYPE.FRAGMENT if frag_total > 1 else msg_type
            
            header = MeshHeader(
                msg_type=actual_type,
                msg_id=msg_id,
                fragment_num=frag_num,
                fragment_total=frag_total,
                origin_node=self.node_id,
                from_node=self.node_id,
                to_node=to_node,
                hop_count=0,
                max_hops=self.max_hops,
                need_ack=need_ack and (frag_num == frag_total - 1),  # ACK только на последний
                is_mesh=True,
                timestamp=timestamp
            )
            
            packet = MeshPacket(header, chunk)
            
            if self.lora.send_raw(packet.to_bytes()):
                self.stats['tx'] += 1
            else:
                log(f"Frag {frag_num+1} FAIL", LOG.ERROR)
                return None
            
            if frag_num < frag_total - 1:
                time.sleep_ms(delay_ms)
        
        # Ограничение размера seen_messages
        self._limit_dict(self.seen_messages, self.MAX_SEEN_MESSAGES)
        self.seen_messages[msg_id] = time.ticks_ms()
        
        # Добавляем в ожидание ACK
        f need_ack:
            self._limit_dict(self.pending_acks, self.MAX_PENDING_ACKS)
            self.pending_acks[msg_id] = {
                'timestamp': time.ticks_ms(),
                'retries': self.max_retries,
                'to_node': to_node,
                'data': data_bytes,
                'msg_type': msg_type
            }
        
        return msg_id
    
    def send_ack(self, original_header):
        """Отправить ACK"""
        header = MeshHeader(
            msg_type=MSG_TYPE.ACK,
            msg_id=original_header.msg_id,
            origin_node=self.node_id,
            from_node=self.node_id,
            to_node=original_header.origin_node,
            hop_count=0,
            max_hops=original_header.max_hops,
            is_mesh=True
        )
        
        packet = MeshPacket(header, b'')
        if self.lora.send_raw(packet.to_bytes()):
            self.stats['acks_sent'] += 1
            log(f"ACK sent for 0x{original_header.msg_id:06X}", LOG.DEBUG)
            return True
        return False
    
    # -------------------------------------------------------------------------
    # РЕТРАНСЛЯЦИЯ
    # -------------------------------------------------------------------------
    
    def _relay_packet(self, header, data):
        """Ретранслировать пакет"""
        if not self.relay_enabled or not header.can_relay():
            if not header.can_relay():
                self.stats['dropped_ttl'] += 1
            return False
        
        # Новый заголовок с увеличенным hop_count
        new_header = MeshHeader(
            msg_type=header.msg_type,
            msg_id=header.msg_id,
            fragment_num=header.fragment_num,
            fragment_total=header.fragment_total,
            origin_node=header.origin_node,
            from_node=self.node_id,  # мы ретранслятор
            to_node=header.to_node,
            hop_count=header.hop_count + 1,
            max_hops=header.max_hops,
            need_ack=header.need_ack,
            is_mesh=header.is_mesh,
            timestamp=header.timestamp
        )
        
        packet = MeshPacket(new_header, data)
        
        # Случайная задержка
        delay = random.randint(self.relay_delay_min_ms, self.relay_delay_max_ms)
        time.sleep_ms(delay)
        
        if self.lora.send_raw(packet.to_bytes()):
            self.stats['relayed'] += 1
            log(f"RELAY: 0x{header.msg_id:06X}", LOG.DEBUG)
            return True
        return False
    
    # -------------------------------------------------------------------------
    # ПРИЕМ И ОБРАБОТКА
    # -------------------------------------------------------------------------
    
    def poll(self):
        """
        Опросить входящие данные и обработать.
        Возвращает список готовых сообщений: [(header, data_bytes), ...]
        """
        self._cleanup()
        self._check_ack_timeouts()
        
        # Читаем все доступные пакеты
        while self.lora.available():
            raw = self.lora.receive_raw(timeout_ms=200)
            if raw is None or len(raw) < MeshHeader.SIZE:
                continue
            
            try:
                packet = MeshPacket.from_bytes(raw)
                header = packet.header
                data = packet.data
            except Exception as e:
                log(f"Parse error: {e}", LOG.ERROR)
                continue
            
            self.stats['rx'] += 1
            self._process_packet(header, data)
        
        # Ограничение completed_messages
        result = self.completed_messages[:self.MAX_COMPLETED_MESSAGES]
        self.completed_messages = []
        return result
    
    def _process_packet(self, header, data):
        """Обработка одного пакета"""
        msg_id = header.msg_id
        
        # 1. Проверка на дубликат
        if msg_id in self.seen_messages:
            self.stats['dropped_duplicate'] += 1
            return
        
        # Запоминаем
        self._limit_dict(self.seen_messages, self.MAX_SEEN_MESSAGES)
        self.seen_messages[msg_id] = time.ticks_ms()
        
        # 2. Это наше сообщение?
        if header.origin_node == self.node_id:
            return
        
        # 3. Обработка ACK
        if header.msg_type == MSG_TYPE.ACK:
            self._process_ack(header)
            # ACK тоже ретранслируем если не для нас
            if header.to_node != self.node_id:
                self._relay_packet(header, data)
            return
        
        # 4. Для нас ли сообщение?
        is_for_me = (header.to_node == self.node_id or 
                     header.to_node == MSG_TARGET.ALL)
        
        # 5. Обрабатываем если для нас
        if is_for_me:
            if header.fragment_total > 1:
                self._process_fragment(header, data)
            else:
                self._complete_message(header, data)
        
        # 6. Ретрансляция
        # Для unicast — ретранслируем если не для нас
        # Для broadcast с mesh — тоже ретранслируем
        if header.to_node != MSG_TARGET.ALL and not is_for_me:
            self._relay_packet(header, data)
        elif header.to_node == MSG_TARGET.ALL and header.is_mesh:
            self._relay_packet(header, data)
    
    def _process_ack(self, header):
        """Обработка входящего ACK"""
        msg_id = header.msg_id
        
        if header.to_node == self.node_id and msg_id in self.pending_acks:
            del self.pending_acks[msg_id]
            self.stats['acks_received'] += 1
            log(f"ACK received: 0x{msg_id:06X}", LOG.INFO)
    
    def _process_fragment(self, header, data):
        """Обработка фрагмента"""
        msg_id = header.msg_id
        
        if msg_id not in self.assembly_buffers:
            self._limit_dict(self.assembly_buffers, self.MAX_ASSEMBLY_BUFFERS)
            self.assembly_buffers[msg_id] = {
                'header': header,
                'total': header.fragment_total,
                'fragments': {},
                'timestamp': time.ticks_ms()
            }
        
        buf = self.assembly_buffers[msg_id]
        frag_num = header.fragment_num
        
        if frag_num in buf['fragments']:
            return  # Дубликат
        
        buf['fragments'][frag_num] = data
        log(f"Frag {frag_num+1}/{buf['total']} for 0x{msg_id:06X}", LOG.DEBUG)
        
        # Все получены?
        if len(buf['fragments']) == buf['total']:
            full_data = b''
            for i in range(buf['total']):
                if i in buf['fragments']:
                    full_data += buf['fragments'][i]
                else:
                    log(f"Missing frag {i}", LOG.ERROR)
                    del self.assembly_buffers[msg_id]
                    return
            
            self._complete_message(buf['header'], full_data)
            del self.assembly_buffers[msg_id]
    
    def _complete_message(self, header, data):
        """Сообщение полностью получено"""
        # Убираем trailing нули
        data = data.rstrip(b'\x00')
        
        log(f"✓ MSG from {header.origin_node}, 0x{header.msg_id:06X}, {len(data)}B", LOG.INFO)
        
        # Отправляем ACK
        if header.need_ack:
            self.send_ack(header)
        
        self.completed_messages.append((header, data))
    
    def _check_ack_timeouts(self):
        """Проверка таймаутов ACK и переотправка"""
        now = time.ticks_ms()
        to_remove = []
        to_resend = []
        
        for msg_id, info in self.pending_acks.items():
            elapsed = time.ticks_diff(now, info['timestamp'])
            
            if elapsed > self.ack_timeout_ms:
                if info['retries'] > 0:
                    to_resend.append(msg_id)
                else:
                    to_remove.append(msg_id)
                    self.stats['timeouts'] += 1
                    log(f"ACK timeout: 0x{msg_id:06X}", LOG.WARN)
        
        # Удаляем
        for msg_id in to_remove:
            del self.pending_acks[msg_id]
        
        # Переотправляем
        for msg_id in to_resend:
            info = self.pending_acks[msg_id]
            log(f"Resending 0x{msg_id:06X}, retries={info['retries']}", LOG.INFO)
            
            new_msg_id = self.send(
                info['data'],
                to_node=info['to_node'],
                msg_type=info['msg_type'],
                need_ack=True
            )
            
            # Удаляем старую запись
            del self.pending_acks[msg_id]
            
            # Новая запись уже создана в send()
            if new_msg_id and new_msg_id in self.pending_acks:
                self.pending_acks[new_msg_id]['retries'] = info['retries'] - 1
    
    def _cleanup(self):
        """Очистка устаревших буферов"""
        now = time.ticks_ms()
        
        # seen_messages
        expired = [k for k, v in self.seen_messages.items()
                   if time.ticks_diff(now, v) > self.seen_ttl_ms]
        for k in expired:
            del self.seen_messages[k]
        
        # assembly_buffers
        expired = [k for k, v in self.assembly_buffers.items()
                   if time.ticks_diff(now, v['timestamp']) > self.assembly_ttl_ms]
        for k in expired:
            del self.assembly_buffers[k]
            
    def _limit_dict(self, d, max_size):
        """Ограничить размер словаря, удаляя старые записи"""
        while len(d) >= max_size:
            oldest_key = next(iter(d))
            del d[oldest_key]
    
    # -------------------------------------------------------------------------
    # УТИЛИТЫ
    # -------------------------------------------------------------------------
    
    def receive(self):
        """Получить одно сообщение (header, data) или None"""
        messages = self.poll()
        return messages[0] if messages else None
    
    def available(self):
        """Есть ли данные?"""
        return self.lora.available()
    
    def is_ack_pending(self, msg_id):
        """Ожидается ли ACK для сообщения?"""
        return msg_id in self.pending_acks
    
    def get_stats(self):
        """Получить статистику"""
        return self.stats.copy()
    
    def print_stats(self):
        """Вывести статистику"""
        s = self.stats
        print(f"=== Stats (id={self.node_id}) ===")
        print(f"TX:{s['tx']} RX:{s['rx']} Relay:{s['relayed']}")
        print(f"ACK sent:{s['acks_sent']} rcvd:{s['acks_received']}")
        print(f"Drop dup:{s['dropped_duplicate']} ttl:{s['dropped_ttl']}")
