## send_to_chain.py

from web3 import Web3
import json
from config import CONTRACT_ADDRESS, RPC_URL, PRIVATE_KEY

## Connect to local node (hardhat)
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Account (using #0 from Hardhat)
account = w3.eth.account.from_key(PRIVATE_KEY)

# Contract address (the one Hardhat gave you when deploying) and ABI (from artifacts/contracts/inventoryDRO.sol/inventoryDRO.json)
contract_address = CONTRACT_ADDRESS

# Contract ABI (you can get it from artifacts/contracts/inventoryDRO.sol/inventoryDRO.json)
with open("artifacts/contracts/inventoryDRO.sol/inventoryDRO.json") as f:
    abi = json.load(f)["abi"]

contract = w3.eth.contract(address=contract_address, abi=abi)

def update_stock(new_stock):
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.functions.updateStock(int(new_stock)).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'chainId': 31337  # Make sure to use the correct chainId for your network (1337 is common for Hardhat)
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print("Stock updated:", tx_hash.hex())

    return tx_hash

def send_decision(forecast, optimalQ, riskCost):
    tx = contract.functions.recorderDecision(
        int(forecast),
        int(optimalQ),
        int(riskCost)
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'chainId': 31337  # Make sure to use the correct chainId for your network (1337 is common for Hardhat)
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Tx sent: {tx_hash.hex()}")
    return tx_hash
