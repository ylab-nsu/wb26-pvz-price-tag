from prices_printer import prices_view as pr_view
import price_loader
from board_client import board_host
import ujson

def main():
    # data = price_loader.load_price_data()
    # if data is not None:
    #     pr_view.view_price_data(data)
    
    board_data = board_host.get_unsynced_board_data()
    board_json = ujson.loads(board_data)
    board_host.confirm_board(board_json["board_id"])

if __name__ == "__main__":
    main()

