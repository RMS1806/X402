import google.generativeai as genai

# ⚠️ PASTE YOUR KEY HERE
genai.configure(api_key="AIzaSyDDWVkXOngZFXtumObWPAJ3Zj7O_dapIqM")

print("🔍 Scanning available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Found: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")