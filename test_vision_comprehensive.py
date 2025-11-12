#!/usr/bin/env python3
"""Comprehensive test of Chutes Vision API with PDF processing"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient, Message
from pdf2image import convert_from_path
import base64
import io

def test_text_message():
    """Test 1: Regular text messages still work"""
    print("\n" + "="*70)
    print("TEST 1: Regular Text Messages")
    print("="*70)
    
    client = ChutesClient()
    message = Message(role="user", content="What is 2+2?")
    
    response = client.chat_completion(
        messages=[message],
        max_tokens=50
    )
    
    print(f"✓ Text message works!")
    print(f"  Response: {response.content}")
    return True

def test_vision_with_pdf():
    """Test 2: Vision model with PDF→Image→Base64"""
    print("\n" + "="*70)
    print("TEST 2: Vision Model with PDF Processing")
    print("="*70)
    
    pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"
    
    # Convert PDF to image
    print("  Converting PDF...")
    images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
    
    # Encode as base64
    print("  Encoding image...")
    buffered = io.BytesIO()
    images[0].save(buffered, format="PNG", optimize=True)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Create multimodal message
    message = Message(
        role="user",
        content=[
            {
                "type": "text",
                "text": "Extract any standard IDs from this page (format: K.CN.1, K.PR.2, etc.)"
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            }
        ]
    )
    
    print("  Calling vision API...")
    client = ChutesClient()
    response = client.chat_completion(
        messages=[message],
        model="Qwen/Qwen3-VL-235B-A22B-Instruct",
        temperature=0.1,
        max_tokens=500
    )
    
    print(f"✓ Vision API works!")
    print(f"  Response preview: {response.content[:300]}...")
    print(f"  Tokens used: {response.usage.get('total_tokens', 'N/A')}")
    
    # Check if it found standard IDs
    if "K.CN." in response.content or "K.PR." in response.content or "K.CR." in response.content:
        print(f"  ✓ Successfully extracted standard IDs!")
        return True
    else:
        print(f"  ⚠️  No standard IDs found in response")
        return False

def test_message_dataclass():
    """Test 3: Message dataclass handles both formats"""
    print("\n" + "="*70)
    print("TEST 3: Message Dataclass Flexibility")
    print("="*70)
    
    # String content
    msg1 = Message(role="user", content="Hello")
    print(f"✓ String content: {type(msg1.content).__name__}")
    
    # List content
    msg2 = Message(role="user", content=[{"type": "text", "text": "Hi"}])
    print(f"✓ List content: {type(msg2.content).__name__} with {len(msg2.content)} parts")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CHUTES VISION API - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Text Messages", test_text_message()))
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results.append(("Text Messages", False))
    
    try:
        results.append(("Vision with PDF", test_vision_with_pdf()))
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results.append(("Vision with PDF", False))
    
    try:
        results.append(("Message Dataclass", test_message_dataclass()))
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results.append(("Message Dataclass", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Vision API is fully functional.")
    else:
        print("⚠️  SOME TESTS FAILED. Review errors above.")
    print("="*70 + "\n")
    
    sys.exit(0 if all_passed else 1)
