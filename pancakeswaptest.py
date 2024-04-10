from web3 import Web3
from web3.middleware import geth_poa_middleware

from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

with open("swap_router_abi.json", "r") as abi_def:
  swap_router_abi = json.load(abi_def)

with open("wbnb_testnet_abi.json", "r") as wbnb_abi:
  wbnb_testnet_abi = json.load(wbnb_abi)

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

w3.middleware_onion.inject(geth_poa_middleware, layer=0)

if w3.is_connected():
    # print(f"Connected to BSC Testnet")
    print(f"Connected to BSC mainnet")
else:
    # print(f"Failed to connected to BSC testnet")
    print(f"Failed to connected to BSC mainnet")

sender_address = "0x638c1546faE0Ce97E1524563F9AE0c42127DbBeE"

Private_Key = os.getenv("My_Private_Key")
if Private_Key is None:
  raise ValueError("Private key not found")

account_privatekey = w3.eth.account.from_key(Private_Key)

# Pancakeswap swap router, swap router abi is at the top of the code
swap_router_address = "	0x13f4EA83D0bd40E75C8222255bc855a974568Dd4" # smart router mainnnet
# swap_router_address = "0x1b81D678ffb9C0263b24A97847620C99d213eB14" # periphery mainnet
# swap_router_address = "0x9a489505a00cE272eAa5e07Dba6491314CaE3796" # swap router v3, bsc testnet (near the bottom of the address documentation)
# swap_router_address = "0x1b81D678ffb9C0263b24A97847620C99d213eB14" #swap router v3, periphery bsc testnet
swap_router_contract = w3.eth.contract(address=swap_router_address, abi=swap_router_abi)

wbnb_contract_address = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c" # mainnet
wbnb_contract = w3.eth.contract(address=wbnb_contract_address, abi=wbnb_testnet_abi)

# 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c WBNB on mainnet, 0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd WBNB on testnet,
# 0x55d398326f99059fF775485246999027B3197955 USDT on Mainnet, 0x337610d27c682E347C9cD60BD4b3b107C9d34dDd USDT on testnet

# Approve the WBNB spend
amount_in = w3.to_wei(0.005, "ether")
approve_txn = wbnb_contract.functions.approve(swap_router_address, amount_in).build_transaction({
  "from": sender_address,
  "nonce": w3.eth.get_transaction_count(sender_address),
  "gas": 100000,
  "gasPrice": w3.to_wei("1", "gwei")
})

signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, Private_Key)
approve_txn_hash = w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
print(f"Approval TX Hash: {approve_txn_hash.hex()}")

w3.eth.wait_for_transaction_receipt(approve_txn_hash)


# parameters for the swap
params = {
  "tokenIn": Web3.to_checksum_address(wbnb_contract_address), # now its WBNB mainnet
  "tokenOut": Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955"), #USDT mainnet
  "fee": 3000, # fee tier of the pool 0.3%
  "recipient": Web3.to_checksum_address("0x638c1546faE0Ce97E1524563F9AE0c42127DbBeE"), #test wallet address
  "deadline": int(time.time()) + 600, #10 mins from now
  "amountIn": w3.to_wei(0.001, "ether"), #amount of wbnb to swap
  "amountOutMinimum": w3.to_wei(0.01, "ether"), # minimum of USDT you are willing to receive
  "sqrtPriceLimitX96": 0, #no specific limit
}

print(f"{params['deadline']}")

params_tuple = (
  params["tokenIn"],
  params["tokenOut"],
  params["fee"],
  params["recipient"],
  params["deadline"],
  params["amountIn"],
  params["amountOutMinimum"],
  params["sqrtPriceLimitX96"],
)

# prepare transaction
txn = swap_router_contract.functions.exactInputSingle(params_tuple).build_transaction({
  "from": sender_address,
  "value": params["amountIn"],
  "gas": 100000,
  "gasPrice": w3.to_wei("1", "gwei"),
  "nonce": w3.eth.get_transaction_count(sender_address),
   # 'value': is only necessary if swapping the native coin (BNB), otherwise omit
})

signed_txn = w3.eth.account.sign_transaction(txn, Private_Key)
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

print(f"Transaction hash: {tx_hash.hex()}")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if tx_receipt.status == 1:
  print(f"Transaction succeeded")
else:
  print(f"Transaction failed")
