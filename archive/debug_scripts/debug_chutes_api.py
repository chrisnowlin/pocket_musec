#!/usr/bin/env python3
"""Debug Chutes API to find available models and fix vision parser"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.llm.chutes_client import ChutesClient, Message

def test_chutes_connection():
    """Test basic Chutes API connection and list available models"""
    
    logger.info("Testing Chutes API connection...")
    
    try:
        client = ChutesClient()
        logger.info(f"✓ Chutes client initialized")
        logger.info(f"  Base URL: {client.base_url}")
        logger.info(f"  Default model: {client.default_model}")
        logger.info(f"  Embedding model: {client.embedding_model}")
        
        # Test a simple chat completion
        logger.info("Testing basic chat completion...")
        
        messages = [
            Message(role="user", content="Hello, can you respond with 'API working'?")
        ]
        
        response = client.chat_completion(messages)
        logger.info(f"✓ Chat completion successful")
        logger.info(f"  Response: {response.content[:100]}...")
        logger.info(f"  Model: {response.model}")
        logger.info(f"  Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Chutes API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision_models():
    """Test different vision model names to find the correct one"""
    
    logger.info("Testing different vision model names...")
    
    # Potential vision model names to try
    vision_models = [
        "Qwen/Qwen3-VL-235B-A22B-Instruct",  # From config
        "Qwen/Qwen2-VL-7B-Instruct",        # Original in parser
        "Qwen/Qwen2-VL-72B-Instruct",       # Alternative
        "Qwen-VL",                          # Short name
        "qwen-vl",                          # Lowercase
        "Qwen2-VL-7B-Instruct",             # Without Qwen/ prefix
        "Qwen2-VL",                         # Base model
    ]
    
    client = ChutesClient()
    
    for model in vision_models:
        logger.info(f"Testing model: {model}")
        
        try:
            # Test with a simple text message first
            messages = [
                Message(role="user", content="What is 2+2?")
            ]
            
            response = client.chat_completion(messages, model=model)
            logger.info(f"✓ Model {model} works with text")
            
            # If text works, try vision
            logger.info(f"Testing vision capabilities with {model}...")
            
            # Create a simple vision test message
            vision_messages = [
                Message(
                    role="user", 
                    content=[
                        {
                            "type": "text",
                            "text": "What do you see in this image? Just say 'image processed'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                            }
                        }
                    ]
                )
            ]
            
            vision_response = client.chat_completion(vision_messages, model=model)
            logger.info(f"✓ Model {model} works with vision!")
            logger.info(f"  Vision response: {vision_response.content[:100]}...")
            
            return model  # Return the first working vision model
            
        except Exception as e:
            logger.warning(f"✗ Model {model} failed: {e}")
            continue
    
    logger.error("No working vision model found")
    return None

def test_api_endpoints():
    """Test different API endpoints to find the correct one"""
    
    logger.info("Testing different API endpoints...")
    
    endpoints = [
        "https://api.chutes.ai/v1",
        "https://api.chutes.ai/v1/chat/completions",
        "https://chutes.ai/v1",
        "https://chutes.ai/api/v1",
    ]
    
    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")
        
        try:
            # Temporarily modify client base URL
            client = ChutesClient(base_url=endpoint)
            
            messages = [
                Message(role="user", content="Hello")
            ]
            
            response = client.chat_completion(messages)
            logger.info(f"✓ Endpoint {endpoint} works")
            logger.info(f"  Response: {response.content[:50]}...")
            
            return endpoint
            
        except Exception as e:
            logger.warning(f"✗ Endpoint {endpoint} failed: {e}")
            continue
    
    logger.error("No working endpoint found")
    return None

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Chutes API Debugging")
    logger.info("=" * 60)
    
    # Test basic connection
    if not test_chutes_connection():
        logger.error("Basic API connection failed - check API key and network")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    
    # Test vision models
    working_model = test_vision_models()
    
    if working_model:
        logger.info(f"\n✓ Working vision model found: {working_model}")
        logger.info("Update the vision parser to use this model")
    else:
        logger.info("\n✗ No working vision model found")
        logger.info("Testing alternative endpoints...")
        
        # Test alternative endpoints
        working_endpoint = test_api_endpoints()
        
        if working_endpoint:
            logger.info(f"✓ Working endpoint found: {working_endpoint}")
        else:
            logger.error("✗ No working configuration found")
            logger.info("Vision parser will continue using hybrid fallback")