#!/usr/bin/env python3
"""Quick test to check if API is available"""
import asyncio
import aiohttp
import base64
from pathlib import Path

API_KEY = "cpk_b2a69dce82614c318761393792d24224.0c430c6531c953c9a169289fa1ebefdc.72nYsSozwc3lGPVLkmuLoZfrI0nhVhZ9"
ENDPOINT = "https://llm.chutes.ai/v1/chat/completions"
MODEL = "Qwen/Qwen3-VL-235B-A22B-Thinking"

async def test_api():
    """Test if API is responding"""
    print("🔍 Testing API availability...")
    
    # Use a small test image
    test_png = Path("Holistic Musical Thinking/extracted/pages_png/page-0000.png")
    
    if not test_png.exists():
        print("❌ Test image not found")
        return False
    
    with open(test_png, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    content = [
        {"type": "text", "text": "Extract text from this image."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
    ]
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                ENDPOINT,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"📡 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ API is AVAILABLE and working!")
                    print(f"   Response received: {len(result.get('choices', [{}])[0].get('message', {}).get('content', ''))} chars")
                    return True
                elif response.status == 503:
                    print("❌ API is UNAVAILABLE (HTTP 503 - Service Unavailable)")
                    print("   The service infrastructure is down or overloaded")
                    return False
                elif response.status == 429:
                    print("⚠️  API is rate limited (HTTP 429)")
                    print("   Service is available but at capacity")
                    return False
                else:
                    error = await response.text()
                    print(f"❌ API error: {response.status}")
                    print(f"   Error: {error[:200]}")
                    return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api())
    exit(0 if result else 1)
