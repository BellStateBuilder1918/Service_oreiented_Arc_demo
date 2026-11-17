import logging
import threading
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [order] %(message)s")

CUSTOMER_URL = "http://localhost:5001"
INVENTORY_URL = "http://localhost:5002"
TIMEOUT = 3

ORDERS = {}
_counter = 1000
lock = threading.Lock()


class DownstreamError(Exception):
    def __init__(self, service):
        self.service = service


@app.before_request
def log_request():
    logging.info("%s %s", request.method, request.path)


def call(service, method, url, **kwargs):
    try:
        return requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.RequestException:
        raise DownstreamError(service)


def reject(reason, code):
    return jsonify({"status": "REJECTED", "reason": reason}), code


@app.errorhandler(DownstreamError)
def downstream(e):
    return jsonify({"status": "REJECTED",
                    "reason": f"{e.service} is unavailable, please try again later"}), 503


@app.post("/orders")
def create_order():
    global _counter
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return reject("Request body must be JSON", 400)
    for field in ("customer_id", "product_id", "quantity"):
        if field not in data:
            return reject(f"Missing field: {field}", 400)
    cid, pid, qty = data["customer_id"], data["product_id"], data["quantity"]
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (cid, pid, qty)):
        return reject("customer_id, product_id and quantity must be integers", 400)
    if qty <= 0:
        return reject("Quantity must be greater than 0", 400)

    # Step 1: validate customer
    r = call("Customer Service", "GET", f"{CUSTOMER_URL}/customers/{cid}")
    if r.status_code == 404:
        return reject("Customer not found", 400)
    if r.status_code != 200:
        raise DownstreamError("Customer Service")
    if r.json().get("status") != "ACTIVE":
        return reject("Customer is not active", 400)

    # Step 2: check product and stock
    r = call("Inventory Service", "GET", f"{INVENTORY_URL}/products/{pid}")
    if r.status_code == 404:
        return reject("Product not found", 400)
    if r.status_code != 200:
        raise DownstreamError("Inventory Service")
    product = r.json()
    if product["stock"] < qty:
        return reject("Insufficient stock", 409)

    # Step 3: total + simulated payment
    total = product["price"] * qty
    payment = "SUCCESS"

    # Step 4: reserve stock
    r = call("Inventory Service", "POST",
             f"{INVENTORY_URL}/products/{pid}/reserve", json={"quantity": qty})
    if r.status_code == 409:
        return reject("Insufficient stock", 409)
    if r.status_code != 200:
        raise DownstreamError("Inventory Service")

    # Step 5: store order
    with lock:
        _counter += 1
        order_id = f"ORD-{_counter}"
        order = {"order_id": order_id, "status": "CONFIRMED",
                 "total_amount": total, "payment": payment,
                 "customer_id": cid, "product_id": pid, "quantity": qty}
        ORDERS[order_id] = order
    return jsonify({k: order[k] for k in ("order_id", "status", "total_amount", "payment")}), 201


@app.get("/orders/<order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order), 200


if __name__ == "__main__":
    app.run(port=5003)
