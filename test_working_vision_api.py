#!/usr/bin/env python3
"""Test the working Chutes vision API"""

import os
import sys
import base64
import logging
import json
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

def test_working_vision_api():
    """Test the working Chutes vision API with correct endpoint"""
    
    logger.info("Testing working Chutes vision API...")
    
    # Create a simple test image (1x1 red pixel)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # Test vision message
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
                        "url": f"data:image/png;base64,{test_image_base64}"
                    }
                }
            ]
        )
    ]
    
    try:
        # Create client with custom base URL
        client = ChutesClient(base_url="https://llm.chutes.ai/v1")
        
        logger.info(f"Using base URL: {client.base_url}")
        logger.info(f"Using model: {client.default_model}")
        
        # Test vision API
        response = client.chat_completion(
            vision_messages, 
            model="Qwen/Qwen3-VL-235B-A22B-Instruct"
        )
        
        logger.info("✅ Vision API test successful!")
        logger.info(f"Response: {response.content}")
        logger.info(f"Model: {response.model}")
        logger.info(f"Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vision API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_api():
    """Test the text API to confirm it works"""
    
    logger.info("Testing text API...")
    
    try:
        client = ChutesClient(base_url="https://llm.chutes.ai/v1")
        
        messages = [
            Message(role="user", content="What is 2+2? Answer with just the number.")
        ]
        
        response = client.chat_completion(messages)
        logger.info(f"✅ Text API response: {response.content}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Text API test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TESTING WORKING CHUTES API")
    logger.info("=" * 60)
    
    # Test text first
    if test_text_api():
        logger.info("✅ Text API working")
    else:
        logger.error("❌ Text API failed")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    
    # Test vision
    if test_working_vision_api():
        logger.info("✅ Vision API working - ready for production!")
    else:
        logger.error("❌ Vision API failed")