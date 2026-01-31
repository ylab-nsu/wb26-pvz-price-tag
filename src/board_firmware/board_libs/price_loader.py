import ujson
import os

from prices_printer import prices_view as pr_view


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

    with open("data/prices.json", "w") as f:
        ujson.dump(raw, f)


def load_price_data():
    path = "data/prices.json"
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
