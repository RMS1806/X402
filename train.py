import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
from model import DataProcessor

def train():
    print("🚀 Starting Random Forest Training...")
    
    # 1. Fetch Data
    processor = DataProcessor()
    print("📚 Fetching 59 days of 15m data...")
    # We use 59 days to stay safely within Yahoo's 60-day limit
    df = processor.fetch_live_data(period="59d", interval="15m")
    
    if df is None:
        print("❌ Error fetching data.")
        return

    # 2. Add Features
    df = processor.add_indicators(df)
    
    # 3. Create Target
    # "Did the price go UP in the next 4 candles (1 hour)?"
    # shift(-4) looks 4 rows into the future
    df['Target_Price'] = df['Close'].shift(-4)
    df['Target'] = (df['Target_Price'] > df['Close']).astype(int)
    
    # Drop rows with NaNs (the last 4 rows won't have a future target)
    df.dropna(inplace=True)

    # 4. Prepare Features (X) and Target (y)
    feature_cols = ['Log_Ret', 'Vol', 'RSI', 'Momentum']
    X = df[feature_cols]
    y = df['Target']
    
    # 5. Split Data (Train on Past, Test on Future)
    # First 80% for training, Last 20% for testing
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    print(f"📊 Training on {len(X_train)} samples, Testing on {len(X_test)} samples")

    # 6. Train Random Forest
    # n_estimators=100: Build 100 decision trees
    # min_samples_split=50: Don't create a leaf for fewer than 50 samples (Anti-Overfitting)
    model = RandomForestClassifier(n_estimators=100, min_samples_split=50, random_state=42)
    model.fit(X_train, y_train)

    # 7. Evaluate
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print(f"\n✅ Training Complete.")
    print(f"🎯 Accuracy on Test Data: {accuracy:.4f}")
    
    # Check if it's better than a coin flip (0.50)
    if accuracy > 0.50:
        print("💾 Saving model to rf_model.pkl...")
        joblib.dump(model, "rf_model.pkl")
    else:
        print("⚠️ Accuracy too low (<= 50%). Model not saved.")
        print("Tip: Try running at a different time of day or waiting for market conditions to change.")

if __name__ == "__main__":
    train()