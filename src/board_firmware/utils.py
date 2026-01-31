import random
import time

import config_pricer as config
from constants import MSG_TARGET, MSG_TYPE

class RingBuffer:
    def __init__(self, max_size):
        self.max_size = max_size
        self._cur_ind = 0
        self._list = [None] * max_size

    def add(self, elem):
        self._list[self._cur_ind] = elem
        self._cur_ind = (self._cur_ind+1) % self.max_size
    
    # можно будет использовать `if elem in my_ring_buffer`
    def __contains__(self, elem):
        return elem in self._list

def get_info_from_msg(self, msg, index=None):
    """
    msg = f"{_id};{_from};{_to};{_type};{_data};{_timestamp};{_need_ack}"
    
    0 - id
    1 - from
    2 - to
    3 - msg type
    4 - data (helpful info)
    5 - timestamp
    6 - need_ack (1) or not (0)
    """
    answer = msg.split(';')
    
    if index:
        return answer[index]
    
    return answer

def log(text, level):
    if level <= config.LOG_LEVEL:
        print(text)

def get_random_id(mini=config.RANDOM_MIN_INT, maxi=config.RANDOM_MAX_INT):
    # проверка mini <= maxi на пользователе
    # *ибо пользуюемся только мы.*
    return random.randint(mini, maxi)

def create_msg_string(self, data, msg_id=None, target=MSG_TARGET.ALL, msg_type=MSG_TYPE.DATA, need_ack=False) -> int:
    """
    Отправка сообщения
    
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
    _id = msg_id if msg_id else f"{get_random_id()}"
    _from = config.NODE_NAME
    _to = target

    _type = msg_type
    _data = str(data)

    _timestamp = int(time.time())
    _need_ack = 1 if need_ack else 0

    msg = f"{_id};{_from};{_to};{_type};{_data};{_timestamp};{_need_ack}"
    
    return msg


### Утилиты работы с экраном
import ujson
import os
from prices_printer import prices_view as pr_view

def show_price_data(data: pr_view.PriceData):
    """Отображает данные о цене на дисплее"""
    pr_view.view_price_data(data)

def save_price_data(data: pr_view.PriceData):
    try:
        os.stat("data")
    except OSError:
        os.mkdir("data")

    raw = {
        "name": data.name,
        "res_price": {
            "rubs": data.res_price.rubs,
            "kopecks": data.res_price.kopecks
        },
        "discount": None
    }

    if data.discount_data is not None:
        raw["discount"] = {
            "base_price": {
                "rubs": data.discount_data.base_price.rubs,
                "kopecks": data.discount_data.base_price.kopecks
            },
            "discount": data.discount_data.discount
        }

    with open("data_json/prices.json", "w") as f:
        ujson.dump(raw, f)


def load_price_data():
    path = "data_json/prices.json"
    try:
        os.stat(path)
    except OSError:
        return None

    with open(path, "r") as f:
        raw = ujson.load(f)

    if "res_price" not in raw:
        return None
    
    rp_json = raw["res_price"]
    res_price = pr_view.PriceVal(
        rp_json["rubs"],
        rp_json["kopecks"]
    )

    discount_data = None
    if "discount" in raw and raw["discount"] is not None:
        try:
            d = raw["discount"]
            bp = d["base_price"]
            base_price = pr_view.PriceVal(
                bp["rubs"],
                bp["kopecks"]
            )
            discount_data = pr_view.DiscountData(
                base_price,
                d["discount"]
            )
        except:
            return None

    return pr_view.PriceData(
        raw["name"],
        res_price,
        discount_data
    )
