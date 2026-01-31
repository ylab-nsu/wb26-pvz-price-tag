# NODE_ID должен быть = 2 (или 3, 4... для других ценников)

import machine
import time
import json

import config_common as config
from lora_mesh import MeshNode, log, LOG
from constants import MSG_TYPE, MSG_TARGET

# Экран
try:
    import utils_screen
    HAS_SCREEN = True
except:
    HAS_SCREEN = False

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
node = None
button = None
last_heartbeat_ms = 0


def init():
    global node, button, last_heartbeat_ms
    
    # Уникальный ID ценника
    config.NODE_ID = 2
    
    node = MeshNode(config)
    button = machine.Pin(config.PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_UP)
    last_heartbeat_ms = time.ticks_ms()
    
    log(f"[PRICER] Ready. ID={config.NODE_ID}", LOG.INFO)
    
    # Загружаем сохраненную цену
    if HAS_SCREEN:
        try:
            saved = utils_screen.load_price_data()
            if saved:
                utils_screen.show_price_data(saved)
                log("[PRICER] Loaded saved price", LOG.INFO)
        except Exception as e:
            log(f"[PRICER] Load error: {e}", LOG.WARN)


def loop():
    global node, last_heartbeat_ms
    
    current_ms = time.ticks_ms()
    
    # 1. Опрашиваем входящие
    messages = node.poll()
    
    for header, data in messages:
        handle_message(header, data)
    
    # 2. Heartbeat
    if time.ticks_diff(current_ms, last_heartbeat_ms) >= config.SEND_ID_EVERY_X_SECONDS * 1000:
        last_heartbeat_ms = current_ms
        node.send(str(config.NODE_ID), to_node=config.HUB_ID, 
                  msg_type=MSG_TYPE.SEND_ID, need_ack=False)
        log("[PRICER] Heartbeat sent", LOG.DEBUG)
    
    # 3. Тест по кнопке
    if button.value() == 0:
        time.sleep_ms(300)
        msg_id = node.send(f"Hello from {config.NODE_ID}!", 
                           to_node=config.HUB_ID, 
                           msg_type=MSG_TYPE.DATA, need_ack=True)
        log(f"[PRICER] Test sent: 0x{msg_id:06X}", LOG.INFO)


def handle_message(header, data):
    """Обработка входящих сообщений"""
    from_node = header.origin_node
    msg_type = header.msg_type
    
    try:
        text = data.decode('utf-8')
    except:
        text = str(data)
    
    log(f"[PRICER] From {from_node}, type={msg_type}", LOG.INFO)
    
    if msg_type == MSG_TYPE.SET_PRICE:
        try:
            price_data = json.loads(text)
            set_price(price_data)
        except Exception as e:
            log(f"[PRICER] Parse error: {e}", LOG.ERROR)
    
    elif msg_type == MSG_TYPE.PING:
        node.send("PONG", to_node=from_node, msg_type=MSG_TYPE.PONG)


def set_price(price_data):
    """Установка цены"""
    log(f"[PRICER] New price: {price_data}", LOG.INFO)
    
    if HAS_SCREEN:
        try:
            from prices_printer import prices_view as pr_view
            
            res_price = pr_view.PriceVal(
                price_data["res_price"]["rubs"],
                price_data["res_price"]["kopecks"]
            )
            
            discount_data = None
            if "discount" in price_data and price_data["discount"]:
                d = price_data["discount"]
                base_price = pr_view.PriceVal(
                    d["base_price"]["rubs"],
                    d["base_price"]["kopecks"]
                )
                discount_data = pr_view.DiscountData(base_price, d["discount"])
            
            data_obj = pr_view.PriceData(
                price_data.get("name", ""),
                res_price,
                discount_data
            )
            
            utils_screen.show_price_data(data_obj)
            utils_screen.save_price_data(data_obj)
            
            log("[PRICER] Price displayed", LOG.INFO)
            
        except Exception as e:
            log(f"[PRICER] Display error: {e}", LOG.ERROR)
    else:
        # Консольный вывод
        print("=== NEW PRICE ===")
        print(f"Name: {price_data.get('name', 'N/A')}")
        rp = price_data.get('res_price', {})
        print(f"Price: {rp.get('rubs', 0)}.{rp.get('kopecks', 0):02d} RUB")
        if price_data.get('discount'):
            print(f"Discount: {price_data['discount'].get('discount', 0)}%")
        print("=================")


def main():
    init()
    log(f"[PRICER] Starting (ID={config.NODE_ID})...", LOG.INFO)
    
    while True:
        try:
            loop()
        except Exception as e:
            log(f"[PRICER] Error: {e}", LOG.ERROR)
        time.sleep_ms(10)


if __name__ == "__main__":
    main()