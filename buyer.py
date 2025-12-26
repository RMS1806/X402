import time
import requests
from web3 import Web3
from eth_account import Account

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000"
RPC_URL = "https://sepolia.base.org"
USDC_CONTRACT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# ⚠️ PASTE YOUR PRIVATE KEY HERE
PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"
MY_ADDRESS = "0xb2984A80Bcb06Dbe7c1f9849949B8c02A71fbE48"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def log(action, message):
    """Sends status to the Dashboard"""
    print(f"[{action}] {message}") 
    try:
        requests.post(f"{API_URL}/log", json={
            "source": "Agent-007",
            "action": action,
            "message": str(message)
        })
    except:
        print("⚠️ Dashboard offline (Server not running?)")

def run_agent():
    log("START", "Initializing Autonomous Agent...")
    time.sleep(1)
    
    log("WAIT", "Scanning market volatility...")
    time.sleep(1)
    
    try:
        # 1. Negotiate
        log("NEGOTIATE", "Requesting /signal from Market API...")
        resp = requests.get(f"{API_URL}/signal")
        
        if resp.status_code == 402:
            log("NETWORK", "⚠️ HTTP 402: PAYMENT REQUIRED detected.")
            
            price = int(resp.headers['x-402-price'])
            seller = resp.headers['x-402-address']
            
            log("BUY", f"Contract: {price/1_000_000} USDC. Signing transaction...")
            
            # 2. Pay
            usdc = w3.eth.contract(address=USDC_CONTRACT, abi=[
                {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"}
            ])
            
            txn = usdc.functions.transfer(seller, price).build_transaction({
                'chainId': 84532, 
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(MY_ADDRESS),
            })
            
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
            try: raw_bytes = signed_txn.rawTransaction
            except AttributeError: raw_bytes = signed_txn.raw_transaction
            
            tx_hash = w3.eth.send_raw_transaction(raw_bytes).hex()
            log("TX_SENT", f"Broadcasted: {tx_hash[:10]}...")
            
            # 3. Verify & Report
            log("VERIFY", "Waiting for block confirmation...")
            
            for i in range(20): 
                time.sleep(3)
                proof_resp = requests.get(f"{API_URL}/signal", headers={"Authorization": tx_hash})
                
                if proof_resp.status_code == 200:
                    data = proof_resp.json()['data']
                    details = data.get('details', {})
                    
                    # EXTRACT DATA
                    signal = data['signal']
                    conf = data['confidence']
                    reasoning = details.get('Reasoning', 'Analyzing...')
                    rsi = details.get('RSI', 'N/A')
                    mom = details.get('Momentum', '0.00')
                    vol = details.get('Volatility', '0.00')
                    asset = details.get('Asset', 'BTC')
                    
                    # NEW: Get Portfolio Stats (This fixes the PnL Table)
                    pnl = details.get('PnL', 0.0)
                    equity = details.get('Equity', 0.0)
                    
                    # NEW: Get News
                    news = details.get('News', 'No Intel')
                    short_news = (news[:50] + '..') if len(news) > 50 else news
                    
                    # FORMAT LOG STRING (Now includes PnL and Equity)
                    log_msg = f"{signal} ({conf}%) | \"{reasoning}\" | RSI:{rsi} | MOM:{mom} | VOL:{vol} | Asset:{asset} | PnL:{pnl} | Eq:{equity} | NEWS:{short_news}"
                    
                    log("DELIVERED", log_msg)
                    break
                else:
                    log("WAIT", "Verifying payment...")
                    
    except Exception as e:
        log("ERROR", f"Agent Crashed: {str(e)}")

if __name__ == "__main__":
    run_agent()