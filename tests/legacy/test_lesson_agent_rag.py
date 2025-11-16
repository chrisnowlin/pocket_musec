#!/usr/bin/env python3
"""
Test script for enhanced lesson agent with RAG integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lesson_agent_rag():
    """Test the enhanced lesson agent with RAG integration"""
    
    print("🎵 Testing Enhanced Lesson Agent with RAG Integration")
    print("=" * 60)
    
    # Initialize the lesson agent
    try:
        flow = Flow()
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)
        print("✅ Lesson agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize lesson agent: {e}")
        return False
    
    # Test message with musical concepts that should trigger semantic search
    test_message = "I need a 1st grade lesson on rhythm patterns with percussion instruments"
    
    print(f"\n📝 Testing with message: '{test_message}'")
    print("-" * 60)
    
    try:
        # Test message analysis
        print("\n1. Testing message analysis...")
        extracted_info = agent._analyze_user_message(test_message)
        print(f"   Extracted info: {extracted_info}")
        
        # Test semantic search for standards
        print("\n2. Testing semantic search for standards...")
        relevant_standards = agent._get_relevant_standards(extracted_info)
        print(f"   Found {len(relevant_standards)} relevant standards:")
        for i, standard in enumerate(relevant_standards[:3]):
            print(f"     {i+1}. {standard.standard_id}: {standard.standard_text[:100]}...")
        
        # Test teaching strategies context retrieval
        print("\n3. Testing teaching strategies context retrieval...")
        teaching_context = agent._get_teaching_strategies_context(extracted_info)
        print(f"   Found {len(teaching_context)} teaching context items:")
        for i, context in enumerate(teaching_context[:2]):
            print(f"     {i+1}. {context[:150]}...")
        
        # Test assessment guidance context retrieval
        print("\n4. Testing assessment guidance context retrieval...")
        assessment_context = agent._get_assessment_guidance_context(extracted_info)
        print(f"   Found {len(assessment_context)} assessment context items:")
        for i, context in enumerate(assessment_context[:2]):
            print(f"     {i+1}. {context[:150]}...")
        
        # Test lesson context building
        print("\n5. Testing lesson context building with RAG...")
        lesson_context = agent._build_lesson_context_from_conversation()
        print(f"   Grade level: {lesson_context.grade_level}")
        print(f"   Selected standard: {lesson_context.standard_id}")
        print(f"   Teaching context items: {len(lesson_context.teaching_context)}")
        print(f"   Assessment context items: {len(lesson_context.assessment_context)}")
        
        # Test full conversational flow
        print("\n6. Testing full conversational response...")
        response = agent.chat(test_message)
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview: {response[:300]}...")
        
        print("\n✅ All RAG integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_semantic_search_fallback():
    """Test semantic search fallback to keyword search"""
    
    print("\n🔍 Testing Semantic Search Fallback Mechanism")
    print("=" * 60)
    
    try:
        flow = Flow()
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)
        
        # Test with nonexistent grade level to trigger fallback
        extracted_info = {
            "grade_level": "Nonexistent Grade",
            "musical_topics": ["rhythm", "patterns"]
        }
        
        print(f"Testing with grade level: {extracted_info['grade_level']}")
        
        # This should trigger the fallback mechanism
        relevant_standards = agent._get_relevant_standards(extracted_info)
        
        print(f"   Fallback results: {len(relevant_standards)} standards found")
        if relevant_standards:
            print("   ✅ Fallback mechanism working correctly")
        else:
            print("   ⚠️  Fallback returned no results (expected for nonexistent grade)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting RAG Integration Tests for Lesson Agent")
    print("=" * 70)
    
    success1 = test_lesson_agent_rag()
    success2 = test_semantic_search_fallback()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("🎉 All RAG integration tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)