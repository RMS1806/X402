import google.generativeai as genai
import json
import os
import feedparser

# ⚠️ KEEP YOUR KEY HERE
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

class Brain:
    def __init__(self):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # Use Stable Flash
            self.model = genai.GenerativeModel('gemini-flash-latest')
        except Exception as e:
            print(f"❌ Gemini Connection Failed: {e}")
            self.model = None

    def fetch_news(self, ticker="BTC-USD"):
        """
        Scrapes CoinDesk. Accepts 'ticker' argument to match model.py calls.
        """
        try:
            # CoinDesk RSS Feed
            feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
            if feed.entries:
                # Get top 2 headlines
                headlines = [entry.title for entry in feed.entries[:2]]
                return " | ".join(headlines)
            return "No news data available."
        except:
            return "Newsfeed offline."

    def get_decision(self, market_data):
        if not self.model:
            return {"signal": "WAIT", "reasoning": "Brain Offline", "confidence": 0}

        # 1. Fetch News (Using the ticker passed in market_data)
        ticker = market_data.get('ticker', 'BTC-USD')
        news_headlines = self.fetch_news(ticker)
        
        print(f"📰 INTEL ACQUIRED: {news_headlines[:50]}...")

        prompt = f"""
        Act as a crypto trading node. Analyze {ticker} data:
        
        - ML Prediction: {market_data['ml_signal']} ({market_data['ml_conf']}%)
        - RSI: {market_data['rsi']}
        - Momentum: {market_data['momentum']}
        - Volatility: {market_data['volatility']}
        - Risk Mode: {market_data.get('risk_mode', 'BALANCED')}
        
        🌍 GLOBAL INTEL (NEWS):
        "{news_headlines}"
        
        TASK:
        Decide BUY, SELL, or WAIT.
        
        RULES:
        1. If news is NEGATIVE (hacks, bans, SEC), bias towards SELL/WAIT.
        2. If news is POSITIVE (ETF, adoption), bias towards BUY.
        3. News momentum can override technicals.
        
        Reply with VALID JSON ONLY:
        {{"signal": "BUY", "confidence": 80, "reasoning": "Short reason citing news if relevant"}}
        """

        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
            
        except Exception as e:
            print(f"🔴 GEMINI ERROR: {e}")
            return {"signal": "WAIT", "reasoning": "API Error", "confidence": 0}

llm_brain = Brain()