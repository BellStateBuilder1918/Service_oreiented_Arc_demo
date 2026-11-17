import logging
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [inventory] %(message)s")

PRODUCTS = {
    1: {"id": 1, "name": "Smartphone", "price": 50000, "stock": 10},
    2: {"id": 2, "name": "Headphones", "price": 2000, "stock": 50},
    3: {"id": 3, "name": "Laptop", "price": 75000, "stock": 3},
}
lock = threading.Lock()


@app.before_request
def log_request():
    logging.info("%s %s", request.method, request.path)


@app.get("/products/<int:product_id>")
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@app.post("/products/<int:product_id>/reserve")
def reserve(product_id):
    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400
    with lock:
        product = PRODUCTS.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        if product["stock"] < quantity:
            return jsonify({"error": "Insufficient stock"}), 409
        product["stock"] -= quantity
        return jsonify({"id": product_id, "remaining_stock": product["stock"]}), 200


if __name__ == "__main__":
    app.run(port=5002)
