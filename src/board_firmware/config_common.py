# config_common.py
# Конфигурация для ESP32-U + LoRa E32

# --- ИДЕНТИФИКАЦИЯ МОДУЛЯ ---
NODE_ID = 1
HUB_ID = 1

# --- LORA EBYTE E32 (UART2) ---
LORA_M0  = 32
LORA_M1  = 33
LORA_AUX = 25
LORA_RX  = 27  # Это TX пин ESP32 (подключается к RX LoRa)
LORA_TX  = 26  # Это RX пин ESP32 (подключается к TX LoRa)

# Настройки эфира
LORA_UART_NUM = 2      # Используем аппаратный UART2
LORA_BAUDRATE = 9600   # Скорость общения с модулем

# --- ПЕРИФЕРИЯ ---
PIN_BUTTON = 0 # boot кнопка
PIN_LED = 2   # Встроенный синий светодиод

# --- НАСТРОЙКИ MESH ---
MAX_HOPS = 5
RELAY_ENABLED = True

# --- ТАЙМАУТЫ ---
ACK_TIMEOUT_MS = 3000
MAX_SEND_RETRIES = 3
SEND_ID_EVERY_X_SECONDS = 300

# --- БУФЕРЫ ---
MAX_HISTORY_SIZE = 50
SEEN_TTL_MS = 60000
ASSEMBLY_TTL_MS = 30000

# --- RANDOM ---
RANDOM_MIN_INT = 0
RANDOM_MAX_INT = 0xFFFFFF

# --- ЛОГИРОВАНИЕ ---
LOG_LEVEL = 3  # INFO

# --- ПУТИ К ФАЙЛАМ ---
PRICE_DATA_PATH = "data/prices.json"
