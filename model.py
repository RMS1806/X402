import os
import yfinance as yf
import pandas as pd
import numpy as np
import joblib 
import json
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from brain import llm_brain 

# --- 1. DATA PROCESSOR (The Eyes) ---
class DataProcessor:
    def __init__(self):
        self.scaler = StandardScaler()
        
    def fetch_live_data(self, ticker="BTC-USD", period="7d", interval="15m"):
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if df.empty: return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
        except: return None

    def add_indicators(self, df):
        df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
        df['Vol'] = df['Log_Ret'].rolling(window=20).std()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Momentum'] = (df['Close'] - df['SMA_50']) / df['SMA_50']
        df.dropna(inplace=True)
        return df

# --- 2. PORTFOLIO MANAGER (The Wallet) ---
class PortfolioManager:
    def __init__(self, filename="portfolio.json"):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f: return json.load(f)
            except: pass
        # Default State: $10,000 Cash, No Positions
        return {"balance": 10000.0, "positions": [], "history": []}

    def save_data(self):
        with open(self.filename, 'w') as f: json.dump(self.data, f, indent=4)

    def execute_buy(self, ticker, price):
        # Position Size: $1,000 per trade
        if self.data["balance"] >= 1000:
            self.data["balance"] -= 1000
            units = 1000 / price
            self.data["positions"].append({
                "ticker": ticker,
                "entry_price": price,
                "units": units,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.save_data()
            return True
        return False

    def check_exit(self, ticker, current_price):
        # Rule: Sell if profit > 1.5% OR loss > 3% (Stop Loss)
        # Returns: Realized PnL (or 0 if no sale)
        realized_pnl = 0
        active_positions = []
        
        for pos in self.data["positions"]:
            if pos["ticker"] == ticker:
                # Calculate % change
                pct_change = (current_price - pos["entry_price"]) / pos["entry_price"]
                
                # TAKE PROFIT (+1.5%) or STOP LOSS (-3%)
                if pct_change >= 0.015 or pct_change <= -0.03:
                    # Sell!
                    revenue = pos["units"] * current_price
                    profit = revenue - 1000
                    self.data["balance"] += revenue
                    self.data["history"].append({
                        "ticker": ticker,
                        "profit": profit,
                        "exit_price": current_price,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    realized_pnl += profit
                else:
                    active_positions.append(pos) # Keep holding
            else:
                active_positions.append(pos)
        
        self.data["positions"] = active_positions
        self.save_data()
        return realized_pnl

    def get_stats(self):
        # Calculate Total Valuation (Cash + Open Positions)
        # Note: We need current prices for perfect accuracy, but we'll approximate with entry for speed
        equity = self.data["balance"]
        for pos in self.data["positions"]:
            equity += (pos["units"] * pos["entry_price"]) 
            
        pnl_pct = ((equity - 10000) / 10000) * 100
        return {
            "balance": round(self.data["balance"], 2),
            "equity": round(equity, 2),
            "pnl_pct": round(pnl_pct, 2),
            "open_trades": len(self.data["positions"])
        }

# --- 3. THE HYBRID AGENT ---
class HybridAgent:
    def __init__(self):
        self.processor = DataProcessor()
        self.portfolio = PortfolioManager() # <--- Connect Portfolio
        self.models = {}
        self.current_ticker = "BTC-USD"
        self.risk_weight = 0.6 
        self.load_fleet()

    def load_fleet(self):
        tickers = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
        print("🏗️ Loading Model Fleet...")
        for t in tickers:
            path = f"model_{t}.pkl"
            if os.path.exists(path):
                self.models[t] = joblib.load(path)
            else:
                print(f"⚠️ Missing: {t}")

    def set_asset(self, ticker):
        if ticker in self.models:
            self.current_ticker = ticker
            print(f"🔄 Switched Agent Focus to: {ticker}")
            return True
        return False

    def set_risk(self, level):
        try:
            self.risk_weight = float(level)
            return True
        except: return False

    def predict_next_move(self, current_price_seq=None):
        df = self.processor.fetch_live_data(ticker=self.current_ticker)
        if df is None: return {"signal": "ERROR", "confidence": 0}

        df = self.processor.add_indicators(df)
        last_row = df.iloc[-1]
        current_price = last_row['Close']
        
        # 1. CHECK PORTFOLIO FIRST (Auto-Sell Rule)
        # Every time we scan, we check if we should take profit on existing trades
        realized_profit = self.portfolio.check_exit(self.current_ticker, current_price)
        stats = self.portfolio.get_stats()

        # 2. RUN ANALYSIS
        current_model = self.models.get(self.current_ticker)
        features = df[['Log_Ret', 'Vol', 'RSI', 'Momentum']].iloc[-1].values.reshape(1, -1)
        
        ml_vote = 0
        ml_signal = "NEUTRAL"
        ml_conf = 0
        
        if current_model:
            probs = current_model.predict_proba(features)[0]
            if probs[1] > 0.5:
                ml_signal, ml_conf = "BUY", round(probs[1] * 100, 1)
                ml_vote = 1
            else:
                ml_signal, ml_conf = "SELL", round(probs[0] * 100, 1)
                ml_vote = -1

        logic_vote = 0
        if last_row['RSI'] < 30: logic_vote = 1
        elif last_row['RSI'] > 70: logic_vote = -1

        ml_w = self.risk_weight
        logic_w = 1.0 - self.risk_weight
        final_score = (ml_vote * ml_w) + (logic_vote * logic_w)

        risk_mode = "BALANCED"
        if self.risk_weight >= 0.8: risk_mode = "DEGEN"
        elif self.risk_weight <= 0.3: risk_mode = "SAFE"

        market_packet = {
            "ticker": self.current_ticker,
            "risk_mode": risk_mode,
            "ml_signal": ml_signal,
            "ml_conf": ml_conf,
            "rsi": round(last_row['RSI'], 2),
            "momentum": round(last_row['Momentum'], 4),
            "volatility": round(last_row['Vol'], 4),
            "recent_returns": round(last_row['Log_Ret'] * 100, 2)
        }

        # 3. BRAIN DECISION
        decision = llm_brain.get_decision(market_packet)
        
        if decision.get("confidence") == 0:
             if final_score > 0.15: final_signal = "BUY"; final_conf = 50 + (final_score * 50)
             elif final_score < -0.15: final_signal = "SELL"; final_conf = 50 + (abs(final_score) * 50)
             else: final_signal = "WAIT"; final_conf = 0
             reasoning = f"LLM Offline. Using {risk_mode} weights."
        else:
             final_signal = decision.get("signal", "WAIT")
             final_conf = decision.get("confidence", 0)
             reasoning = decision.get("reasoning", "Analysis complete.")

        # 4. EXECUTE TRADE (Paper Trading)
        # ... (Previous code remains the same)

        # 4. EXECUTE TRADE (DEBUG MODE)
        # We print exactly what the Agent is seeing so you can fix the threshold.
        print(f"\n🧐 DEBUG: Signal={final_signal} | Conf={final_conf} | Threshold=10 (TEST)")
        
        trade_status = "Scanning"
        # --- CHEAT CODE: FORCE BUY ---
        # Uncomment the next two lines to force a buy on the next scan:
        
        # TEST RULE: Buy if Signal is BUY and Confidence > 10% (Very Low for Testing)
        if final_signal == "BUY" and float(final_conf) > 10:
            print("🟢 TRIGGER: Buying Condition MET!")
            if self.portfolio.execute_buy(self.current_ticker, current_price):
                trade_status = "OPENED POSITION ($1000)"
                print(f"✅ SUCCESS: Bought {self.current_ticker} at ${current_price}")
            else:
                trade_status = "INSUFFICIENT FUNDS"
                print("❌ FAIL: Not enough fake money in portfolio.json")
        else:
            print("🔴 SKIPPED: Buying Condition NOT met.")

        # If we just sold (Realized Profit), inject that into the reasoning
        if realized_profit > 0:
            reasoning = f"💰 PROFIT TAKEN! Sold position for +${round(realized_profit, 2)}. " + reasoning
            print(f"🎉 SELLING: Realized Profit of ${realized_profit}")

        # ... (Return statement remains the same)

        return {
            "signal": final_signal,
            "confidence": round(float(final_conf), 1),
            "market_price": round(current_price, 2),
            "details": {
                "Asset": self.current_ticker,
                
                # --- I FORGOT THESE LINES IN THE LAST UPDATE ---
                "Momentum": market_packet['momentum'],   # <--- RESTORED
                "Volatility": market_packet['volatility'], # <--- RESTORED
                
                "RSI": market_packet['rsi'],
                "News": llm_brain.fetch_news(self.current_ticker),
                "Reasoning": reasoning,
                "Balance": stats["balance"],
                "Equity": stats["equity"],
                "PnL": stats["pnl_pct"],
                "TradeStatus": trade_status
            }
        }

predictor = HybridAgent()