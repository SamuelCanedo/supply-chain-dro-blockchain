## order_generator.py 

import json 
from datetime import datetime
import os
import time
import uuid 
import random 
from web3 import Web3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONTRACT_ADDRESS, RPC_URL, PRIVATE_KEY

# ______________________________________________________
## Configuration
# ______________________________________________________

ORDER_COOLDOWN = 30  # Time in seconds to avoid duplicate orders
processed_orders = {}  # Dictionary to track recent orders
order_history = []  # History of processed orders

#----------------------------------------
# Blockchain connection configuration
#----------------------------------------

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract_address = CONTRACT_ADDRESS

# Calculate paths correctly
# This file is located at: project/integration/orders/order_generator.py
current_file = os.path.abspath(__file__)  # .../project/integration/orders/order_generator.py
orders_dir = os.path.dirname(current_file)  # .../project/integration/orders
integration_dir = os.path.dirname(orders_dir)  # .../project/integration
project_dir = os.path.dirname(integration_dir)  # .../project

# Correct path to the ABI
abi_path = os.path.join(
    project_dir, 
    "artifacts",
    "contracts", 
    "inventoryDRO.sol", 
    "inventoryDRO.json"
)

print(f"=== DEBUG order_generator ===")
print(f"Project dir: {project_dir}")
print(f"ABI path: {abi_path}")
print(f"ABI exists: {os.path.exists(abi_path)}")
print(f"=============================\n")

## Load ABI

with open(abi_path) as f:
    abi = json.load(f)["abi"]
    print("✅ ABI uploaded successfully")

contract = w3.eth.contract(address=contract_address, abi=abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

#----------------------------------------
# MAIN FUNCTION
#----------------------------------------

def generate_order(quantity):
    """
    Generates a purchase order and confirms it on the blockchain
    Prevents duplicate orders using cooldown
    """    
    # Check if there is a recent order for this quantity
    quantity = int(quantity)
    current_time = time.time()

    if quantity in processed_orders:
        last_order_time = processed_orders[quantity]
        if current_time - last_order_time < ORDER_COOLDOWN:
            print(f"!!! Duplicate order avoided: {quantity}")
            return None
    
    # Create the order
    order_id = f"PO-{uuid.uuid4().hex[:8]}"  # Unique ID for each order

    order = {
        "order_id": order_id,
        "timestamp": datetime.now().isoformat(),
        "quantity": quantity,
        "supplier": random.choice(["Tier1_Bosch", "Tier1_Siemens", "Tier1_Continental"]),
        "status": "CREATED",
        "blockchain_tx": None,
        "confirmed": False
    }

    # Save order to file
    orders_output_dir = os.path.join(project_dir, "orders_output")
    os.makedirs(orders_output_dir, exist_ok=True)

    file_path = os.path.join(orders_output_dir, f"{order_id}.json")

    with open(file_path, "w") as f:
        json.dump(order, f, indent=4)

    print(f"📄 Order created: {order_id} - Quantity: {quantity}")

    # ----------------------------------------
    # Blockchain (secure fallback)
    # ----------------------------------------

    try:
        if not w3.is_connected():
            raise Exception("Could not connect to the blockchain")
        
        # Verify that the contract exists
        code = w3.eth.get_code(contract_address)
        if code == b'':
            raise Exception(f"Contract not deployed")
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build transaction to confirm the order
        tx = contract.functions.confirmOrder(quantity).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'chainId': 31337  # Hardhat chain ID
        })
        
        # Sign and send transaction
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"✅ Transaction sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
                
        if receipt['status'] == 1:
            order["blockchain_tx"] = tx_hash.hex()
            order["confirmed"] = True
            order["block_number"] = receipt['blockNumber']
            order["status"] = "CONFIRMED"

            with open(file_path, "w") as f:
                json.dump(order, f, indent=4)
            
            print(f"✅ Order confirmed in block: {receipt['blockNumber']}")
    
    except Exception as e:
        print(f"!!! Blockchain fallback: {e}")

            
            # Register processed order
    processed_orders[quantity] = current_time

    return order

def get_order_status(order_id):
    """Get the status of an order by its ID"""
    file_path = os.path.join(project_dir, "orders_output", f"{order_id}.json")
    try:
        with open(file_path, "r") as f:
            order = json.load(f)
        return order
    except FileNotFoundError:
        return None

def get_recent_orders(limit=5):
    """Get the most recent orders generated sorted by real time of creation (not blockchain time)"""
    orders_output_dir = os.path.join(project_dir, "orders_output")

    if not os.path.exists(orders_output_dir):
        return []
        
    files = [f for f in os.listdir(orders_output_dir) if f.endswith(".json")]

    files.sort(
        #key = f"{quantity}_{time.time()/30}",  # Sort by creation time (simulated with file modification time)
        key=lambda x: os.path.getmtime(os.path.join(orders_output_dir, x)),
        reverse=True
    )

    orders = []
    for file in files[:limit]:
        with open(os.path.join(orders_output_dir, file), "r") as f:
            orders.append(json.load(f))

    return orders
