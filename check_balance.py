from web3 import Web3

# Use the working RPC from your last step
RPC_URL = "https://base-sepolia-rpc.publicnode.com" 
MY_WALLET = "0xb2984A80Bcb06Dbe7c1f9849949B8c02A71fbE48" # <--- PASTE YOUR ADDRESS

w3 = Web3(Web3.HTTPProvider(RPC_URL))

eth_balance = w3.eth.get_balance(MY_WALLET)
print(f"💰 ETH Balance: {eth_balance / 10**18} ETH")

if eth_balance == 0:
    print("❌ STILL 0. Go use the faucet again!")
else:
    print("✅ READY! You have gas money.")