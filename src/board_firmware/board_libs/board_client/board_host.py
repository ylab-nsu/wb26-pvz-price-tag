import urequests

from .wifi_init import connect_wifi
from config import HOST, GATEWAY_TOKEN

connect_wifi()
HEADERS = {"Authorization": f"Bearer {GATEWAY_TOKEN}"}

def get_unsynced_board_data() -> str | None:
    try:
        url = f"{HOST}/board_host/unsync_board"
        resp = urequests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            data = resp.text
            return data
        else:
            resp.close()
            return None
    except Exception as e:
        print("Error fetching board:", e)
        return None

def confirm_board(board_id: str) -> bool:
    try:
        url = f"{HOST}/board_host/confirm_board"
        payload = {"board_id": board_id}
        resp = urequests.post(url, json=payload, headers=HEADERS)
        resp.close()
        return resp.status_code == 200
    except Exception as e:
        print("Error confirming board:", e)
        return False

