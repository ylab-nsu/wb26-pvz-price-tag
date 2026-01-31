# config_pricer.py
# Конфигурация для ESP32-U + LoRa E32

# --- ИДЕНТИФИКАЦИЯ МОДУЛЯ ---
NODE_ID = "PRICER_1"

# --- LORA EBYTE E32 (UART2) ---
LORA_M0  = 32
LORA_M1  = 33
LORA_AUX = 25
LORA_RX  = 26  # Это TX пин ESP32 (подключается к RX LoRa)
LORA_TX  = 27  # Это RX пин ESP32 (подключается к TX LoRa)

# Настройки эфира
LORA_UART_NUM = 2      # Используем аппаратный UART2
LORA_BAUDRATE = 9600   # Скорость общения с модулем

# --- ПЕРИФЕРИЯ ---
PIN_BUTTON = 0 # boot кнопка
PIN_LED = 2   # Встроенный синий светодиод

###
###
MAX_HISTORY_SIZE = 100  # Количество ID для хранения в истории
SEND_ID_EVERY_X_SECONDS = 60*60 # 1*hour

MAX_SEND_RETRIES = 3

RANDOM_MIN_INT = 0
RANDOM_MAX_INT = 9999 # включительно

###
###

LOG_LEVEL = 1
