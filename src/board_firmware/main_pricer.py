# main.py
import machine
import time
import random

import config_pricer as config
from lora_mini import LoRaMini
import utils
from constants import MSG_FIELD, MSG_TYPE, LOG

lora = None
history = None
button = None

wait_acks = None # TODO лимит на размер, превратить в deque/RingBuffer

last_id_sent_ms = 0

def init():
    global lora, history, button, wait_acks, last_id_sent_ms
    # Инициализация
    lora = LoRaMini(config)
    button = machine.Pin(config.PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)

    history = utils.RingBuffer(config.MAX_HISTORY_SIZE)
    wait_acks = {} # empty dict

    last_id_sent_ms = time.ticks_ms()

utils.log(f"""
    \n=== Pricer: {config.NODE_ID} ===
    press BOOT - send msg
    also waiting msg...\n
""", level=LOG.INFO)


def loop():
    global lora, history, button, wait_acks, last_id_sent_ms

    current_ms = time.ticks_ms()
    
    msg = lora.receive_msg(timeout=LoRaMini.MSG_READ_TIMEOUT)

    # если получили сообщение из LoRa-mesh
    if msg != None:
        parsed = utils.get_info_from_msg(msg)
        msg_id, _from, _to, msg_type, _data, _timestamp, _need_ack = parsed

        if msg_id in history:
            # skip packet
            utils.log("[INFO] Packet have been already", level=LOG.INFO)
            return

        # добавим в нашу историю послежних пакетов, чтоб не повторяться в будущем
        history.add(msg_id)

        # не нам — дальше передаём и пропускаем обработку
        if _to != config.NODE_ID:
            resend_msg(_data)
            return

        # если сообщение всё-таки нам
        if msg_type == MSG_TYPE.DATA:
            # сейчас мы уверены, что сообщения от хаба содержат только новую цену
            # и других сообщений от хаба быть не может
            try:
                utils.show_price_data(_data)
            except Exception as e:
                utils.log(f"[ERROR] Failed to set price: {e}", level=LOG.ERROR)
        elif msg_type == MSG_TYPE.ACK:
            utils.log("[ACK] Got ack-packet from {_from}")
            # _data это только id пакета
            if _data in wait_acks:
                del wait_acks[_data]
        
        if _need_ack:
            # никто не запрещает запросить ack-пакет на ack-пакет, в принципе
            # но код пишу я (вроде адекватный) — постараюсь такой хернёй не маяться
            send_ack(msg_id, _from)
    
    # Если настало время напомнить шлюзу о нашем существовании
    # (например, шлюз раз в час будет удалять наш ID из таблицы, якобы ценник разрядился/сломался)
    # (но мы будем напоминать шлюзу, что всё ещё живы и работаем)
    if time.ticks_diff(current_ms, last_id_sent_ms) >= config.SEND_ID_EVERY_X_SECONDS * 1000:
        last_id_sent_ms = current_ms

        msg_id = utils.get_random_id()
        msg = utils.create_msg_string(data=config.NODE_ID, msg_id=msg_id, target=config.HUB_ID, msg_type=MSG_TYPE.SEND_ID, need_ack=True)
        lora.send_string(msg)
        add_wait_ack(msg_id, msg)
    
    # проверяем, получены ли ack пакеты вовремя. Если нет (и попытки ещё есть) — переотправляем
    keys_to_resend = []
    keys_to_remove = []
    for key, value in wait_acks.items():
        if value[2] <= 0:
            keys_to_remove.append(key)
        if time.ticks_diff(time.ticks_ms(), value[0]) > LoRaMini.ACK_TIMEOUT:
            keys_to_resend.append(key)

    for key in keys_to_remove:
        del wait_acks[key]
        utils.log(f"[INFO] Message {key} removed after max retries", level=LOG.INFO)
        
    for key in keys_to_resend:
        value = wait_acks[key]
        lora.send_string(value[1])
        wait_acks[key] = (time.ticks_ms(), value[1], value[2] - 1)


def set_price(price_data):
    utils.show_price_data(price_data)

def send_ack(msg_id, device_to):
    lora.send_msg(msg_id, target=device_to, msg_type=MSG_TYPE.ACK)

def resend_msg(data):
    lora.send_string(data)

def add_wait_ack(msg_id, msg):
    global wait_acks
    wait_acks[msg_id] = (time.ticks_ms(), msg, config.MAX_SEND_RETRIES)



def main():
    init()
    while True:
        loop()

if __name__ == "__main__":
    main()
