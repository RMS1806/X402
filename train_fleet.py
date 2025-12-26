import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from model import DataProcessor

# LIST OF ASSETS TO TRAIN
ASSETS = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]

def train_asset(ticker):
    print(f"\n🚀 Training Agent for: {ticker}...")
    
    processor = DataProcessor()
    # Fetch 59 days of history for THIS specific coin
    df = processor.fetch_live_data(ticker=ticker, period="59d", interval="15m")
    
    if df is None or len(df) < 100:
        print(f"❌ Not enough data for {ticker}")
        return

    df = processor.add_indicators(df)
    
    # Target: Price UP in 1 hour (4 candles)
    df['Target_Price'] = df['Close'].shift(-4)
    df['Target'] = (df['Target_Price'] > df['Close']).astype(int)
    df.dropna(inplace=True)

    feature_cols = ['Log_Ret', 'Vol', 'RSI', 'Momentum']
    X = df[feature_cols]
    y = df['Target']
    
    # Train
    split = int(len(X) * 0.8)
    model = RandomForestClassifier(n_estimators=100, min_samples_split=50, random_state=42)
    model.fit(X.iloc[:split], y.iloc[:split])
    
    # Evaluate
    acc = accuracy_score(y.iloc[split:], model.predict(X.iloc[split:]))
    print(f"🎯 {ticker} Accuracy: {acc:.4f}")
    
    # SAVE with the Ticker Name
    filename = f"model_{ticker}.pkl"
    joblib.dump(model, filename)
    print(f"💾 Brain Saved: {filename}")

if __name__ == "__main__":
    for coin in ASSETS:
        train_asset(coin)