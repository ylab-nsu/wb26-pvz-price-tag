# NODE_ID должен быть = 1

import machine
import time
import json

import config_common as config
from lora_mesh import MeshNode, log, LOG
from constants import MSG_TYPE, MSG_TARGET

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
node = None
button = None
test_counter = 0

# === ТЕСТОВЫЕ ДАННЫЕ ===
PRICE_DATA_1 = {
    "name": "Tea Greenfield",
    "res_price": {"rubs": 122, "kopecks": 99}
}

PRICE_DATA_2 = {
    "name": "Tea Greenfield",
    "res_price": {"rubs": 99, "kopecks": 99},
    "discount": {
        "base_price": {"rubs": 122, "kopecks": 99},
        "discount": 23
    }
}


def init():
    global node, button
    
    # Устанавливаем ID хаба
    config.NODE_ID = 1
    
    node = MeshNode(config)
    button = machine.Pin(config.PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
    
    log(f"[HUB] Ready. ID={config.NODE_ID}", LOG.INFO)


def loop():
    global node, test_counter
    
    # 1. Опрашиваем входящие
    messages = node.poll()
    
    for header, data in messages:
        handle_message(header, data)
    
    # 2. Отправка по кнопке
    if button.value() == 0:
        time.sleep_ms(300)
        
        price_data = PRICE_DATA_2 if test_counter % 2 else PRICE_DATA_1
        test_counter += 1
        
        send_price(2, price_data)  # Отправляем на ценник ID=2


def handle_message(header, data):
    """Обработка входящих сообщений"""
    from_node = header.origin_node
    msg_type = header.msg_type
    
    try:
        text = data.decode('utf-8')
    except:
        text = str(data)
    
    log(f"[HUB] From {from_node}: {text[:50]}", LOG.INFO)
    
    if msg_type == MSG_TYPE.SEND_ID:
        log(f"[HUB] Pricer {from_node} online", LOG.INFO)
    elif msg_type == MSG_TYPE.PING:
        node.send("PONG", to_node=from_node, msg_type=MSG_TYPE.PONG)


def send_price(pricer_id, price_data):
    """Отправка цены на ценник"""
    try:
        json_str = json.dumps(price_data)
        
        msg_id = node.send(
            json_str,
            to_node=pricer_id,
            msg_type=MSG_TYPE.SET_PRICE,
            need_ack=True
        )
        
        if msg_id:
            log(f"[HUB] Price sent to {pricer_id}, msg=0x{msg_id:06X}", LOG.INFO)
        else:
            log(f"[HUB] Send failed", LOG.ERROR)
            
    except Exception as e:
        log(f"[HUB] Error: {e}", LOG.ERROR)


def main():
    init()
    log("[HUB] Starting...", LOG.INFO)
    
    while True:
        try:
            loop()
        except Exception as e:
            log(f"[HUB] Error: {e}", LOG.ERROR)
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
