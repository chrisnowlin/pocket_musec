#!/usr/bin/env python3
"""Test script to verify Chutes API connectivity"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_api_connection():
    """Test if we can connect to Chutes API"""

    print("=" * 60)
    print("CHUTES API CONNECTION TEST")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking Environment Variables...")
    print("-" * 60)

    api_key = os.getenv('CHUTES_API_KEY')
    base_url = os.getenv('CHUTES_API_BASE_URL', 'https://llm.chutes.ai/v1')

    if api_key:
        # Mask the API key for security
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✓ CHUTES_API_KEY: {masked_key}")
    else:
        print("✗ CHUTES_API_KEY: Not set")
        print("\n⚠️  API key is required to make API calls.")
        print("   Set it with: export CHUTES_API_KEY=your_api_key")
        print("   Or create a .env file with: CHUTES_API_KEY=your_api_key")
        return False

    print(f"✓ CHUTES_API_BASE_URL: {base_url}")

    # Try to import and initialize the client
    print("\n2. Initializing Chutes Client...")
    print("-" * 60)

    try:
        from backend.llm.chutes_client import ChutesClient, Message
        print("✓ Successfully imported ChutesClient")

        client = ChutesClient()
        print("✓ Successfully initialized ChutesClient")
        print(f"  - Base URL: {client.base_url}")
        print(f"  - Default Model: {client.default_model}")
        print(f"  - Timeout: {client.timeout}s")

    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    # Try a simple API call
    print("\n3. Testing Simple API Call...")
    print("-" * 60)

    try:
        messages = [
            Message(role="user", content="Say 'Hello, API is working!' and nothing else.")
        ]

        print("Sending test message to API...")
        response = client.chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.1
        )

        print(f"✓ API Response received!")
        print(f"  - Model: {response.model}")
        print(f"  - Finish Reason: {response.finish_reason}")
        print(f"  - Content: {response.content}")

        if response.usage:
            print(f"  - Tokens used: {response.usage}")

    except Exception as e:
        print(f"✗ API call failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False

    # Try a vision API call
    print("\n4. Testing Vision API Call...")
    print("-" * 60)

    try:
        import base64
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageFont

        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)

        # Draw some text
        text = "Test Image\nVision API Test"
        draw.text((50, 50), text, fill='black')

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Create multimodal message
        messages = [
            Message(
                role="user",
                content=[
                    {
                        "type": "text",
                        "text": "What text do you see in this image? Reply with just the text you see."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            )
        ]

        print("Sending test image to vision API...")
        response = client.chat_completion(
            messages=messages,
            model="Qwen/Qwen3-VL-235B-A22B-Instruct",
            max_tokens=100,
            temperature=0.1
        )

        print(f"✓ Vision API Response received!")
        print(f"  - Model: {response.model}")
        print(f"  - Content: {response.content}")

    except Exception as e:
        print(f"⚠️  Vision API call failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        print("  (This is optional - text API is working)")

    # Success!
    print("\n" + "=" * 60)
    print("✅ SUCCESS: Chutes API is fully functional!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
