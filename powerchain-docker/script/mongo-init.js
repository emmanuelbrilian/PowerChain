print("Start creating databases")

db = db.getSiblingDB('powerchain');
db.createCollection("users")
db.createCollection("purchase_orders")
db.createCollection("notifications")

print("Databases created")
