#!/usr/bin/env python3
"""Test different API formats to find the correct Chutes API structure"""

import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = "cpk_b2a69dce82614c318761393792d24224.0c430c6531c953c9a169289fa1ebefdc.72nYsSozwc3lGPVLkmuLoZfrI0nhVhZ9"

def test_endpoint(url, description):
    """Test a specific endpoint"""
    print(f"\nTesting: {description}")
    print(f"URL: {url}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✓ SUCCESS!")
            return True
        else:
            print("✗ Failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_chat_endpoint(url, description):
    """Test a chat completions endpoint"""
    print(f"\nTesting: {description}")
    print(f"URL: {url}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✓ SUCCESS!")
            return True
        else:
            print("✗ Failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Chutes API Formats")
    print("=" * 60)
    
    # Test base endpoints
    base_endpoints = [
        ("https://api.chutes.ai/v1/models", "Models endpoint"),
        ("https://api.chutes.ai/v1/", "Base v1 endpoint"),
        ("https://api.chutes.ai/models", "Models without v1"),
        ("https://api.chutes.ai/", "Base endpoint"),
        ("https://chutes.ai/api/v1/models", "Alternative domain models"),
        ("https://chutes.ai/api/models", "Alternative domain models without v1"),
    ]
    
    for url, desc in base_endpoints:
        if test_endpoint(url, desc):
            break
        time.sleep(1)  # Avoid rate limiting
    
    print("\n" + "=" * 60)
    print("Testing Chat Completions Formats")
    print("=" * 60)
    
    # Test chat endpoints
    chat_endpoints = [
        ("https://api.chutes.ai/v1/chat/completions", "Standard OpenAI format"),
        ("https://api.chutes.ai/v1/completions", "Completions endpoint"),
        ("https://api.chutes.ai/chat/completions", "Chat without v1"),
        ("https://chutes.ai/api/v1/chat/completions", "Alternative domain"),
        ("https://chutes.ai/v1/chat/completions", "Alternative without api"),
    ]
    
    for url, desc in chat_endpoints:
        if test_chat_endpoint(url, desc):
            break
        time.sleep(2)  # Avoid rate limiting

if __name__ == "__main__":
    main()