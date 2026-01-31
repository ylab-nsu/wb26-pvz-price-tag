import time
import network
from config import WIFI_SSID, WIFI_PASS

is_connected = False


def connect_wifi():
    global is_connected
    if is_connected:
        return

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        try:
            wlan.connect(WIFI_SSID, WIFI_PASS)
            for i in range(20):
                if wlan.isconnected():
                    break
                time.sleep(1)
        except:
            pass

    if wlan.isconnected():
        print("WIFI: Успешно!")
        is_connected = True
    else:
        raise Exception("Ошибка подключения WIFI")
