## blockchain.py

from web3 import Web3
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


## Initialize Web3 and contract


json_path = os.path.join(project_root, "blockchain", "artifacts", "contracts", "inventoryDRO.sol", "inventoryDRO.json")

with open(json_path) as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# After creating w3, add this:
print(f"Checking contract at: {CONTRACT_ADDRESS}")
code = w3.eth.get_code(CONTRACT_ADDRESS)
print(f"Contract code length: {len(code)}")
print(f"Is contract: {code != b''}")
print(f"Connected: {w3.is_connected()}")
print(f"Contract has code: {w3.eth.get_code(CONTRACT_ADDRESS) != b''}")

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)


def get_status():
    w3.middleware_onion.clear()  # Clean middleware to avoid stale data issues
    result = contract.functions.getStatus().call()

    return {
        "stock": result[0],
        "reorder_point": result[1],
        "shortage": result[2],
        "last_order": result[3],
        "cooldown": result[4],
        "connected": True
    }

def set_reorder_point(new_reorder_point):
    """Update the reorder point on the blockchain"""
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        
        tx = contract.functions.setReorderPoint(new_reorder_point).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'chainId': 31337
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Reorder point updated: {new_reorder_point}")
        return receipt['status'] == 1
    except Exception as e:
        print(f"❌ Error updating reorder point: {e}")
        return False