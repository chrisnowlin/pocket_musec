#!/usr/bin/env python3
"""Simple integration test for citation system"""

import asyncio
import json
import requests
import re


async def test_citations():
    """Test lesson generation with citations"""
    print("🧪 Testing Citation System Integration\n")

    base_url = "http://localhost:8000"

    # Create session
    print("1. Creating session...")
    session_response = requests.post(
        f"{base_url}/api/sessions",
        json={"grade_level": "Third Grade"},
        headers={"Content-Type": "application/json"},
    )

    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.status_code}")
        return False

    session_id = session_response.json().get("id")
    print(f"✅ Session created: {session_id}")

    # Send lesson request
    print("\n2. Requesting lesson plan...")
    lesson_request = {
        "message": "I need a lesson plan for third grade music class. Generate lesson plan now.",
        "enable_web_search": True,
    }

    chat_response = requests.post(
        f"{base_url}/api/sessions/{session_id}/messages",
        json=lesson_request,
        headers={"Content-Type": "application/json"},
    )

    if chat_response.status_code != 200:
        print(f"❌ Failed to send message: {chat_response.status_code}")
        print(chat_response.text)
        return False

    response_data = chat_response.json()
    ai_response = response_data.get("response", "")
    print("✅ Received AI response")

    # Check for citations
    print("\n3. Checking for citations...")

    has_bibliography = "## Web Sources References" in ai_response
    has_urls = "http" in ai_response

    print(f"Has bibliography: {has_bibliography}")
    print(f"Has URLs: {has_urls}")

    if has_bibliography:
        print("\n📚 Bibliography found!")
        # Show excerpt
        lines = ai_response.split("\n")
        bib_start = -1
        for i, line in enumerate(lines):
            if "## Web Sources References" in line:
                bib_start = i
                break

        if bib_start >= 0:
            print("\n".join(lines[bib_start : bib_start + 10]))

    if has_urls:
        urls = re.findall(r"https?://[^\s\)]+", ai_response)
        print(f"\n🔗 Found {len(urls)} URLs")
        for url in urls[:3]:
            print(f"  - {url}")

    # Success criteria
    success = has_bibliography or has_urls

    if success:
        print("\n✅ SUCCESS: Citations are working!")
    else:
        print("\n❌ FAILED: No citations found")
        print("\nResponse excerpt:")
        print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)

    return success


if __name__ == "__main__":
    success = asyncio.run(test_citations())
    exit(0 if success else 1)
