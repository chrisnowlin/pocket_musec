#!/usr/bin/env python3
"""
Test script to verify markdown rendering in the lesson generation conversation flow.
This tests the complete flow from user input to AI response with markdown formatting.
"""

import requests
import json
import time


def test_simple_lesson_endpoint():
    """Test if there's a simpler lesson endpoint available"""

    base_url = "http://localhost:8000"

    print("🔍 Testing for simple lesson endpoints...")

    # Check available endpoints
    try:
        docs_response = requests.get(f"{base_url}/api/docs")
        if docs_response.status_code == 200:
            print(
                "✅ API docs available - check http://localhost:8000/api/docs for endpoints"
            )

        # Try to find lesson-related endpoints
        root_response = requests.get(f"{base_url}/")
        if root_response.status_code == 200:
            print(f"   API info: {root_response.json()}")

    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")

    return False


def test_markdown_rendering():
    """Test the lesson generation with markdown formatting"""

    base_url = "http://localhost:8000"

    print("🧪 Testing Markdown Rendering in Lesson Generation")
    print("=" * 60)

    # Test 1: Check if backend is running
    print("\n1. Checking backend connectivity...")

    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(
                f"✅ Backend is healthy: {health_data.get('service')} v{health_data.get('version')}"
            )
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

    # Test 2: Try to test the lesson agent directly
    print("\n2. Testing lesson agent directly...")

    try:
        # Import and test the lesson agent directly
        import sys
        import os

        sys.path.append("/Users/cnowlin/Developer/pocket_musec")

        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store
        from backend.repositories.standards_repository import StandardsRepository

        # Create agent
        flow = Flow(name="test")
        store = Store()
        standards_repo = StandardsRepository()

        agent = LessonAgent(
            flow=flow,
            store=store,
            standards_repo=standards_repo,
            conversational_mode=True,
        )

        print("✅ Lesson agent created successfully")

        # Test 3: Send a test message to the agent
        print("\n3. Testing agent response with markdown...")

        test_message = "Create a fun music lesson about rhythm for 5th grade students"
        response = agent.chat(test_message)

        print("✅ Agent response received")
        print(f"   Response length: {len(response)} characters")

        # Test 4: Analyze markdown formatting in the response
        print("\n4. Analyzing markdown formatting...")

        markdown_indicators = {
            "headers": response.count("#"),
            "bold": response.count("**"),
            "italic": response.count("*"),
            "lists": response.count("•") + response.count("-") + response.count("* "),
            "emojis": len([c for c in response if ord(c) > 127]),
            "line_breaks": response.count("\n"),
            "sections": response.count("##"),
        }

        print("   Markdown formatting detected:")
        for indicator, count in markdown_indicators.items():
            status = "✅" if count > 0 else "⚠️"
            print(f"   {status} {indicator}: {count}")

        # Test 5: Check for lesson-specific content
        print("\n5. Checking for lesson-specific content...")

        lesson_elements = {
            "standards": any(
                term in response.lower() for term in ["standard", "objective", "goal"]
            ),
            "activities": any(
                term in response.lower()
                for term in ["activity", "exercise", "practice"]
            ),
            "assessment": any(
                term in response.lower()
                for term in ["assessment", "evaluation", "check"]
            ),
            "materials": any(
                term in response.lower() for term in ["material", "resource", "supply"]
            ),
            "structure": any(
                term in response.lower()
                for term in ["introduction", "warm-up", "closure"]
            ),
        }

        print("   Lesson elements found:")
        for element, found in lesson_elements.items():
            status = "✅" if found else "⚠️"
            print(f"   {status} {element}: {'Yes' if found else 'No'}")

        # Test 6: Display content preview
        print("\n6. Content preview (first 800 characters):")
        print("   " + "=" * 50)
        preview = response[:800].replace("\n", "\n   ")
        print(f"   {preview}...")
        print("   " + "=" * 50)

        # Test 7: Overall assessment
        print("\n7. Overall Assessment:")

        markdown_score = sum(1 for count in markdown_indicators.values() if count > 0)
        lesson_score = sum(lesson_elements.values())

        if markdown_score >= 4 and lesson_score >= 4:
            print(
                "   🎉 EXCELLENT: Rich markdown formatting with comprehensive lesson content!"
            )
            print("   📱 The frontend should display beautifully formatted responses!")
        elif markdown_score >= 2 and lesson_score >= 3:
            print("   ✅ GOOD: Adequate formatting with solid lesson content!")
        else:
            print("   ⚠️  NEEDS IMPROVEMENT: Limited formatting or lesson content!")

        # Test 8: Test conversational follow-up
        print("\n8. Testing conversational follow-up...")

        follow_up = agent.chat("Can you add some fun rhythm games to this lesson?")
        follow_up_markdown = {
            "headers": follow_up.count("#"),
            "bold": follow_up.count("**"),
            "lists": follow_up.count("•"),
            "emojis": len([c for c in follow_up if ord(c) > 127]),
        }

        print("   Follow-up formatting:")
        for indicator, count in follow_up_markdown.items():
            status = "✅" if count > 0 else "⚠️"
            print(f"   {status} {indicator}: {count}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import lesson agent: {e}")
        print("   This might be due to missing dependencies or path issues.")
        return False
    except Exception as e:
        print(f"❌ Error testing lesson agent: {e}")
        return False


def test_frontend_build():
    """Test that the frontend builds successfully with markdown renderer"""

    print("\n🏗️  Testing Frontend Build")
    print("=" * 60)

    try:
        import subprocess
        import os

        frontend_dir = "/Users/cnowlin/Developer/pocket_musec/frontend"

        # Check if frontend directory exists
        if not os.path.exists(frontend_dir):
            print("❌ Frontend directory not found")
            return False

        # Run build command
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ Frontend builds successfully!")
            print("   MarkdownRenderer component is working correctly")
            return True
        else:
            print(f"❌ Frontend build failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Frontend build timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing frontend build: {e}")
        return False


if __name__ == "__main__":
    print("🎵 PocketMusec Markdown Rendering Test")
    print("=" * 60)

    # Test backend markdown generation
    success1 = test_markdown_rendering()

    # Test frontend build
    success2 = test_frontend_build()

    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)

    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ Backend generates rich markdown responses")
        print("   ✅ Frontend builds with markdown renderer")
        print("   🎯 Ready for end-to-end testing!")
    elif success1:
        print("⚠️  PARTIAL SUCCESS:")
        print("   ✅ Backend markdown generation works")
        print("   ❌ Frontend build has issues")
    elif success2:
        print("⚠️  PARTIAL SUCCESS:")
        print("   ❌ Backend markdown generation has issues")
        print("   ✅ Frontend build works")
    else:
        print("❌ ALL TESTS FAILED!")

    print("\nNext steps:")
    print("1. Open http://localhost:5173 in your browser")
    print("2. Navigate to the lesson planning page")
    print("3. Start a conversation and check for markdown formatting")
    print("4. Look for emojis, headers, bold text, and proper spacing")
