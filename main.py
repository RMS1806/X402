from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
import datetime
import subprocess
import sys

# Import our Hybrid Agent
from model import predictor 

app = FastAPI()

# --- CONFIGURATION ---
RPC_URL = "https://sepolia.base.org" 
SELLER_ADDRESS = "0xb2984A80Bcb06Dbe7c1f9849949B8c02A71fbE48" 
USDC_CONTRACT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e" 
PRICE_USDC = 1.0 

w3 = Web3(Web3.HTTPProvider(RPC_URL))

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
    expose_headers=["x-402-price", "x-402-address", "x-402-token"]
)

agent_logs = []

class LogEntry(BaseModel):
    source: str; action: str; message: str; timestamp: str = None

@app.post("/log")
async def add_log(entry: LogEntry):
    entry.timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    agent_logs.insert(0, entry) 
    return {"status": "Logged"}

@app.get("/logs")
async def get_logs(): return agent_logs[:50] 

@app.get("/clear_logs")
async def clear_logs():
    global agent_logs
    agent_logs = []
    return {"status": "Cleared"}

# --- ASSET & RISK MANAGEMENT ---
class AssetRequest(BaseModel): ticker: str
class RiskRequest(BaseModel): level: float

@app.post("/set_asset")
async def set_asset(req: AssetRequest):
    success = predictor.set_asset(req.ticker)
    return {"status": "success", "asset": req.ticker} if success else {"status": "error"}

@app.post("/set_risk")
async def set_risk(req: RiskRequest):
    success = predictor.set_risk(req.level)
    return {"status": "success", "risk": req.level} if success else {"status": "error"}

# --- AGENT TRIGGER ---
@app.post("/trigger_agent")
async def trigger_agent():
    print("🚀 USER COMMAND: Executing Autonomous Agent...")
    subprocess.Popen([sys.executable, "buyer.py"])
    return {"status": "started", "message": "Agent process spawned"}

# --- PAYMENT VERIFICATION ---
def verify_payment(tx_hash: str):
    print(f"\n🕵️ VERIFYING TX: {tx_hash}")
    try:
        try: receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        except: return False
        if receipt['status'] != 1: return False

        tx = w3.eth.get_transaction(tx_hash)
        input_data = tx['input']
        if hasattr(input_data, 'hex'): input_data = input_data.hex()
        input_data = str(input_data).lower()
        if not input_data.startswith("0x"): input_data = "0x" + input_data

        if tx['to'].lower() != USDC_CONTRACT.lower(): return False
        if not input_data.startswith("0xa9059cbb"): return False
        
        params = input_data[10:]
        if ("0x" + params[24:64]).lower() != SELLER_ADDRESS.lower(): return False

        print("✅ PAYMENT VERIFIED!")
        return True
    except: return False

@app.get("/signal")
async def get_signal(authorization: str = Header(None)):
    if not authorization:
        headers = { "x-402-price": str(int(PRICE_USDC * 1_000_000)), "x-402-address": SELLER_ADDRESS, "x-402-token": USDC_CONTRACT }
        return Response(status_code=402, headers=headers)

    if verify_payment(authorization):
        prediction = predictor.predict_next_move()
        print(f"✅ DELIVERED: {prediction['signal']} ({prediction['confidence']}%)")
        return {"status": "PAID", "data": prediction}
    else:
        raise HTTPException(status_code=403, detail="Invalid Transaction")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)