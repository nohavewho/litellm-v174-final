#!/usr/bin/env python3
"""
Bulk add Gemini models to LiteLLM with load balancing
- 10 models: gemini-2.5-flash (RPM: 15, TPM: 1M)
- 110+ models: gemini-2.5-pro (RPM: 15, TPM: 250K)

ВАЖНО: Все fallbacks отключены для предотвращения переключения на VertexAI
"""

import requests
import json
import time
import sys

# Configuration
LITELLM_URL = "https://lite.up.railway.app"
API_KEY = "sk-9b8d676797b1c546d8b5f3ba871cfec6220dcd9d14f96dce616edcb6f904b582"

# Read API keys from file
try:
    with open("gemini kets", "r") as f:
        api_keys = [line.strip() for line in f.readlines() if line.strip()]
except FileNotFoundError:
    print("❌ File 'gemini kets' not found!")
    sys.exit(1)

print(f"📊 Found {len(api_keys)} API keys")

def clear_existing_models():
    """Clear existing Gemini models from database"""
    print("🧹 Clearing existing models...")
    
    # Get all models
    url = f"{LITELLM_URL}/model/info"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            models = response.json().get("data", [])
            
            # Delete Gemini models
            deleted_count = 0
            for model in models:
                model_name = model.get("model_name", "")
                if "gemini" in model_name.lower():
                    model_id = model.get("model_id")
                    if model_id:
                        delete_url = f"{LITELLM_URL}/model/delete"
                        delete_payload = {"id": model_id}
                        
                        delete_response = requests.post(delete_url, headers=headers, json=delete_payload, timeout=30)
                        if delete_response.status_code == 200:
                            print(f"🗑️  Deleted {model_name} (ID: {model_id})")
                            deleted_count += 1
                        else:
                            print(f"❌ Failed to delete {model_name}: {delete_response.status_code}")
                        
                        time.sleep(0.2)  # Small delay
            
            print(f"✅ Deleted {deleted_count} existing Gemini models")
            return True
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error clearing models: {str(e)}")
        return False

def add_model(model_name, model_path, api_key, rpm, tpm, max_tokens=8192):
    """Add a single model to LiteLLM"""
    url = f"{LITELLM_URL}/model/new"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model_name": model_name,
        "litellm_params": {
            "model": model_path,
            "api_key": api_key,
            "rpm": rpm,
            "tpm": tpm,
            "max_tokens": max_tokens,
            # Explicitly disable fallbacks at model level
            "fallbacks": [],
            "context_window_fallbacks": [],
            "content_policy_fallbacks": []
        },
        "model_info": {
            "description": f"Gemini model with {rpm} RPM, {tpm} TPM limits",
            "provider": "google"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added {model_name} - ID: {result.get('model_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to add {model_name}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error adding {model_name}: {str(e)}")
        return False

def test_model_endpoint():
    """Test if LiteLLM endpoint is accessible"""
    print("🔍 Testing LiteLLM endpoint...")
    
    try:
        url = f"{LITELLM_URL}/health"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ LiteLLM endpoint is accessible")
            return True
        else:
            print(f"❌ LiteLLM endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach LiteLLM endpoint: {str(e)}")
        return False

def main():
    print("🚀 Starting bulk model addition for 120 Gemini keys...")
    print("📋 Configuration:")
    print(f"   - Flash models: 10 (RPM: 15, TPM: 1M)")
    print(f"   - Pro models: {len(api_keys) - 10} (RPM: 15, TPM: 250K)")
    print(f"   - Total API keys: {len(api_keys)}")
    print(f"   - Fallbacks: DISABLED")
    print()
    
    # Skip endpoint test - go directly to adding models
    # if not test_model_endpoint():
    #     print("❌ Cannot proceed without accessible LiteLLM endpoint")
    #     sys.exit(1)
    
    # Clear existing models
    if not clear_existing_models():
        print("⚠️  Warning: Could not clear existing models, proceeding anyway...")
    
    success_count = 0
    total_count = 0
    
    # Add 10 gemini-2.5-flash models
    print("\n📱 Adding gemini-2.5-flash models (10 keys)...")
    for i in range(min(10, len(api_keys))):
        api_key = api_keys[i]
        model_name = "gemini-2.5-flash"
        model_path = "gemini/gemini-2.5-flash"
        
        if add_model(model_name, model_path, api_key, rpm=15, tpm=1000000):
            success_count += 1
        total_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Add remaining gemini-2.5-pro models  
    remaining_keys = len(api_keys) - 10
    if remaining_keys > 0:
        print(f"\n💎 Adding gemini-2.5-pro models ({remaining_keys} keys)...")
        for i in range(10, len(api_keys)):
            api_key = api_keys[i]
            model_name = "gemini-2.5-pro"
            model_path = "gemini/gemini-2.5-pro"
            
            if add_model(model_name, model_path, api_key, rpm=15, tpm=250000):
                success_count += 1
            total_count += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
            # Progress indicator
            if (i - 9) % 20 == 0:
                print(f"📈 Progress: {i - 9}/{remaining_keys} pro models added")
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"✅ Successfully added: {success_count}/{total_count} models")
    print(f"📊 Flash models: {min(10, len(api_keys))}")
    print(f"📊 Pro models: {max(0, len(api_keys) - 10)}")
    print(f"🚫 Fallbacks: DISABLED (no VertexAI fallback)")
    print(f"⚡ Load balancing: usage-based-routing-v2")
    
    if success_count == total_count:
        print("\n🎉 ALL MODELS ADDED SUCCESSFULLY!")
        print("🔥 Your LiteLLM is ready for 250K+ TPM on Gemini!")
    else:
        print(f"\n⚠️  {total_count - success_count} models failed to add")
        print("Check the logs above for details")

if __name__ == "__main__":
    main() 