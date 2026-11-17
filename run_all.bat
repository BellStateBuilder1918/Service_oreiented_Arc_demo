@echo off
start "Customer 5001" cmd /k python customer_service\app.py
start "Inventory 5002" cmd /k python inventory_service\app.py
start "Order 5003" cmd /k python order_service\app.py
