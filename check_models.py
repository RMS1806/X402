import google.generativeai as genai

# ⚠️ PASTE YOUR KEY HERE
genai.configure(api_key="YOUR_GEMINI_API_KEY")

print("🔍 Scanning available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Found: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")
