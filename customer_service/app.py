import logging
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [customer] %(message)s")

CUSTOMERS = {
    101: {"id": 101, "name": "Alice Sharma", "status": "ACTIVE"},
    102: {"id": 102, "name": "Bob Verma", "status": "ACTIVE"},
    103: {"id": 103, "name": "Carol Singh", "status": "INACTIVE"},
}


@app.before_request
def log_request():
    logging.info("%s %s", request.method, request.path)


@app.get("/customers/<int:customer_id>")
def get_customer(customer_id):
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer), 200


if __name__ == "__main__":
    app.run(port=5001)
