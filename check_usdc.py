from web3 import Web3

# 1. Config
RPC_URL = "https://base-sepolia-rpc.publicnode.com"
MY_WALLET = "0xb2984A80Bcb06Dbe7c1f9849949B8c02A71fbE48" # <--- PASTE YOUR ADDRESS
USDC_CONTRACT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e" #

# 2. Connect
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 3. Ask the Contract for Balance
# (We need a tiny ABI to ask for 'balanceOf')
ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

contract = w3.eth.contract(address=USDC_CONTRACT, abi=ABI)
balance = contract.functions.balanceOf(MY_WALLET).call()

# 4. Print Result
print(f"💰 USDC Balance: {balance / 1000000} USDC") #

if balance < 1000000:
    print("❌ ERROR: You are broke! You need at least 1.0 USDC.")
else:
    print("✅ SUCCESS: You have funds. The error is something else.")