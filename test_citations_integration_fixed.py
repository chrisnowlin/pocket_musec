#!/usr/bin/env python3
"""Integration test for citation system in lesson generation"""

import asyncio
import json
import requests
import time
import re


async def test_lesson_generation_with_citations():
    """Test lesson generation with web search and citations"""
    print("🔍 Testing Lesson Generation with Citations\n")

    # API endpoint
    base_url = "http://localhost:8000"

    # Start a new conversation session
    session_data = {
        "grade_level": "Third Grade",
        "musical_focus": ["rhythm", "percussion"],
        "lesson_duration": "45 minutes",
        "class_size": 25,
    }

    try:
        # Create session
        print("1. Creating session...")
        session_response = requests.post(
            f"{base_url}/api/sessions",
            json=session_data,
            headers={"Content-Type": "application/json"},
        )

        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.status_code}")
            print(session_response.text)
            return False

        session_id = session_response.json().get("id")
        print(f"✅ Session created: {session_id}")

        # Send a message to trigger lesson generation
        print("\n2. Sending lesson request...")
lesson_request = {
            "message": "I need a music education lesson plan. Please generate a complete lesson plan.",
            "enable_web_search": True
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

        # Check for citations in the response
        print("\n3. Analyzing response for citations...")

        # Check if there's a bibliography section
        has_bibliography = "## Web Sources References" in ai_response
        has_citations = "[" in ai_response and "http" in ai_response

        print(f"Has bibliography section: {has_bibliography}")
        print(f"Has citation markers: {has_citations}")

        if has_bibliography:
            print("\n📚 Bibliography found:")
            # Extract bibliography section
            lines = ai_response.split("\n")
            in_bibliography = False
            bibliography_lines = []

            for line in lines:
                if "## Web Sources References" in line:
                    in_bibliography = True
                    bibliography_lines.append(line)
                elif in_bibliography:
                    if line.strip() == "" and len(bibliography_lines) > 1:
                        break
                    bibliography_lines.append(line)

            print("\n".join(bibliography_lines[:10]))  # Show first 10 lines

        if has_citations:
            print("\n🔗 Citation URLs found:")
            # Extract URLs from the response
            urls = re.findall(r"https?://[^\s\)]+", ai_response)
            for i, url in enumerate(urls[:5], 1):  # Show first 5 URLs
                print(f"{i}. {url}")

        # Check for inline citations
        inline_citations = re.findall(r"\[Web Source: \d+", ai_response)
        if inline_citations:
            print(f"\n📝 Found {len(inline_citations)} inline citations")

        # Overall assessment
        print("\n4. Overall Assessment:")
        if has_bibliography and has_citations:
            print("✅ SUCCESS: Citation system is working correctly!")
            print("   - Bibliography section present")
            print("   - Citation URLs included")
            print("   - Lesson plan generated with web search integration")
            return True
        elif has_citations:
            print("⚠️  PARTIAL: Citations found but no bibliography section")
            print("   - URLs are included in the response")
            print("   - May need to check bibliography generation")
            return True
        else:
            print("❌ FAILED: No citations found in response")
            print("   - Web search may not be working")
            print("   - Citation integration may need fixes")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Integration Test: Citation System in Lesson Generation\n")

    success = asyncio.run(test_lesson_generation_with_citations())

    if success:
        print("\n🎉 Integration test completed successfully!")
    else:
        print("\n💥 Integration test failed!")
        exit(1)
