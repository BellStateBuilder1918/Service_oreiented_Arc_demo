# SOA Case Study: Online Shopping Order Processing

*Case Study on Web Service (REST) – Service-Oriented Architecture*

## 1. Problem Statement

An online store must process customer orders reliably. Customer verification, stock checking, payment and order confirmation are separate business capabilities that different teams or systems may own. If they are built as one monolithic program, any change affects everything and none of the pieces can be reused.

This case study builds a small order-processing system as **independent web services** that communicate only through HTTP and JSON, following Service-Oriented Architecture (SOA) principles.

## 2. Architecture

The system has three services, each running as its own Flask server on its own port, plus a service consumer.

| Component | Role | Port |
| --- | --- | --- |
| Postman | Service consumer (client) | – |
| Order Service | Service provider and orchestrator | 5003 |
| Customer Service | Service provider | 5001 |
| Inventory Service | Service provider | 5002 |

```
            HTTP/JSON
Postman ───────────────► Order Service (5003)
                           │        │
              GET /customers/{id}   │  GET /products/{id}
                           ▼        ▼  POST /products/{id}/reserve
                   Customer Service   Inventory Service
                       (5001)             (5002)
```

The Order Service is the only service the client talks to. It calls the other two over HTTP, simulates payment, and returns the final result. Customer and Inventory services know nothing about each other or about the Order Service, which gives loose coupling.

## 3. Service Contracts

### Customer Service (port 5001)

| Method | Endpoint | Description | Success | Failure |
| --- | --- | --- | --- | --- |
| GET | /customers/{id} | Validate and fetch a customer | 200 `{id, name, status}` | 404 `{error: "Customer not found"}` |

### Inventory Service (port 5002)

| Method | Endpoint | Description | Success | Failure |
| --- | --- | --- | --- | --- |
| GET | /products/{id} | Get product, price and stock | 200 `{id, name, price, stock}` | 404 `{error: "Product not found"}` |
| POST | /products/{id}/reserve | Reduce stock by `quantity` | 200 `{id, remaining_stock}` | 409 `{error: "Insufficient stock"}` |

### Order Service (port 5003)

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | /orders | Place an order |
| GET | /orders/{order\_id} | Retrieve an order's status |

Sample request to `POST /orders`:

```json
{ "customer_id": 101, "product_id": 1, "quantity": 2 }
```

Sample success response (201):

```json
{ "order_id": "ORD-1001", "status": "CONFIRMED", "total_amount": 100000, "payment": "SUCCESS" }
```

Sample rejection (400 or 409):

```json
{ "status": "REJECTED", "reason": "Insufficient stock" }
```

## 4. Workflow (Service Orchestration)

1. Client sends `POST /orders` to the Order Service.
2. Order Service validates the request body (required fields, quantity > 0).
3. Order Service calls Customer Service to validate the customer. If not found, the order is rejected.
4. Order Service calls Inventory Service to check price and stock. If stock is insufficient, the order is rejected.
5. Order Service calculates the total (price × quantity) and simulates payment, which succeeds for valid orders.
6. Order Service calls Inventory Service to reserve (reduce) the stock.
7. Order Service stores the order, generates an order ID and returns the confirmation to the client.

If any downstream service is unreachable, the Order Service returns 503 with a clear message instead of crashing.

## 5. Technologies Used

- **Python Flask** to expose each service as a RESTful web service
- **JSON** as the message format
- **HTTP GET and POST** as the operations
- **requests** library for service-to-service calls
- **Postman** as the service consumer for demonstration
- In-memory dictionaries as data stores (no database needed for a toy model)

## 6. SOA Principles Demonstrated

| Principle | How it appears in this project |
| --- | --- |
| Service Provider | Customer, Inventory and Order services |
| Service Consumer | Postman, and the Order Service when it calls the others |
| Loose Coupling | Services interact only through HTTP APIs and share no code or data |
| Service Contract | Fixed endpoints and JSON request/response formats (Section 3) |
| Reusability | Customer validation can be reused by any other application |
| Service Enablement | Flask exposes each capability as a REST API |
| Service Integration | Order Service integrates the other two over HTTP |
| Service Orchestration | Order Service coordinates the full order workflow |
| Governance | Input validation, consistent error codes, request logging |
| Interoperability | Standard HTTP and JSON, so any client or language can consume the services |

## 7. Demonstration Plan

1. Start the three services in three separate terminals.
2. Call `GET /customers/101` to show customer validation.
3. Call `GET /products/1` to show available stock.
4. Call `POST /orders` for a valid order and show the confirmation.
5. Call `GET /products/1` again to show stock has decreased.
6. Place an invalid order (unknown customer, then excessive quantity) and show the rejection.
7. Optionally stop the Inventory Service and place an order to show the 503 handling.

## 8. Possible Viva Questions

- Why is this SOA and not just a Python program? *Each service is an independent process with its own port, reachable only through a defined HTTP contract.*
- Why REST instead of SOAP? *Lightweight, JSON-based, simpler to implement and test; SOAP adds XML/WSDL overhead that this scope doesn't need.*
- What is orchestration? *The Order Service controls the sequence and logic of calls across services.*
- What would you add for production? *A database per service, authentication, an API gateway, retries/timeouts and a compensation step if payment fails after stock reservation.*
