#!/usr/bin/env python3
"""Two-step test for citation system"""

import asyncio
import json
import requests
import re


async def test_citations_two_step():
    """Test lesson generation with citations using two-step approach"""
    print("🧪 Testing Citation System (Two-Step)\n")

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

    # Step 1: Provide lesson information
    print("\n2. Providing lesson information...")
    info_request = {
        "message": "I need a music education lesson about rhythm for my third grade class.",
        "enable_web_search": True,
    }

    info_response = requests.post(
        f"{base_url}/api/sessions/{session_id}/messages",
        json=info_request,
        headers={"Content-Type": "application/json"},
    )

    if info_response.status_code != 200:
        print(f"❌ Failed to send info: {info_response.status_code}")
        return False

    print("✅ Provided lesson information")

    # Step 2: Request lesson generation
    print("\n3. Requesting lesson generation...")
    lesson_request = {"message": "generate lesson plan", "enable_web_search": True}

    lesson_response = requests.post(
        f"{base_url}/api/sessions/{session_id}/messages",
        json=lesson_request,
        headers={"Content-Type": "application/json"},
    )

    if lesson_response.status_code != 200:
        print(f"❌ Failed to generate lesson: {lesson_response.status_code}")
        print(lesson_response.text)
        return False

    response_data = lesson_response.json()
    ai_response = response_data.get("response", "")
    print("✅ Received lesson response")

    # Check for citations
    print("\n4. Checking for citations...")

    has_bibliography = "## Web Sources References" in ai_response
    has_urls = "http" in ai_response
    has_lesson_content = "lesson plan" in ai_response.lower() or len(ai_response) > 1000

    print(f"Has bibliography: {has_bibliography}")
    print(f"Has URLs: {has_urls}")
    print(f"Has lesson content: {has_lesson_content}")

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

    # Show response excerpt
    print(f"\n📝 Response excerpt (first 500 chars):")
    print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)

    # Success criteria
    success = has_lesson_content and (has_bibliography or has_urls)

    if success:
        print("\n✅ SUCCESS: Lesson generated with citations!")
    else:
        print("\n❌ RESULT: Lesson generation or citations not working properly")

    return success


if __name__ == "__main__":
    success = asyncio.run(test_citations_two_step())
    exit(0 if success else 1)
