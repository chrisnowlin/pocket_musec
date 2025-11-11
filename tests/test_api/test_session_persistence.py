"""Tests for session persistence and agent state restoration"""

import pytest
import json
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.session_repository import SessionRepository
from backend.repositories.models import Standard


class TestAgentStateSerialization:
    """Test agent state serialization and deserialization"""

    def test_serialize_empty_agent(self):
        """Test serializing an agent with no state"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        state_json = agent.serialize_state()
        assert state_json is not None

        # Should be valid JSON
        state = json.loads(state_json)
        assert "current_state" in state
        assert "lesson_requirements" in state
        assert "conversation_history" in state

    def test_serialize_agent_with_data(self):
        """Test serializing an agent with conversation data"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Simulate some conversation
        agent.chat("Hi")
        agent.chat("1")  # Select grade

        state_json = agent.serialize_state()
        state = json.loads(state_json)

        # Should have conversation history
        assert len(state["conversation_history"]) > 0

        # Should have current state
        assert state["current_state"] is not None

    def test_restore_agent_state(self):
        """Test restoring agent state from JSON"""
        flow1 = Flow(name="test1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)

        # Have a conversation
        agent1.chat("Hi")
        agent1.chat("1")

        # Serialize state
        state_json = agent1.serialize_state()
        original_state = agent1.get_state()

        # Create new agent and restore
        flow2 = Flow(name="test2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)

        agent2.restore_state(state_json)

        # States should match
        assert agent2.get_state() == original_state

    def test_restore_preserves_requirements(self):
        """Test that restoration preserves lesson requirements"""
        flow1 = Flow(name="test1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)

        # Add some requirements
        agent1.lesson_requirements["grade_level"] = "Grade 3"
        agent1.lesson_requirements["strand_code"] = "CN"
        agent1.lesson_requirements["duration"] = "30 minutes"

        # Serialize and restore
        state_json = agent1.serialize_state()

        flow2 = Flow(name="test2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)
        agent2.restore_state(state_json)

        # Requirements should be preserved
        assert agent2.lesson_requirements["grade_level"] == "Grade 3"
        assert agent2.lesson_requirements["strand_code"] == "CN"
        assert agent2.lesson_requirements["duration"] == "30 minutes"


class TestSessionPersistence:
    """Test session persistence in database"""

    def test_save_agent_state_to_session(self):
        """Test saving agent state to session"""
        repo = SessionRepository()

        # Create a session
        session = repo.create_session(
            user_id="test-user", grade_level="Grade 3", strand_code="CN"
        )

        # Create agent with some state
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)
        agent.chat("Hi")

        # Save state
        state_json = agent.serialize_state()
        history_json = json.dumps(agent.get_conversation_history())
        current_state = agent.get_state()

        updated_session = repo.save_agent_state(
            session_id=session.id,
            agent_state=state_json,
            conversation_history=history_json,
            current_state=current_state,
        )

        # Verify state was saved
        assert updated_session is not None
        assert updated_session.agent_state == state_json
        assert updated_session.conversation_history == history_json
        assert updated_session.current_state == current_state

    def test_restore_session_with_agent_state(self):
        """Test restoring agent from session"""
        repo = SessionRepository()

        # Create session with agent state
        session = repo.create_session(user_id="test-user", grade_level="Grade 3")

        # Create and save agent state
        flow1 = Flow(name="test1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)
        agent1.chat("Hi")
        agent1.chat("1")

        state_json = agent1.serialize_state()
        history_json = json.dumps(agent1.get_conversation_history())
        current_state = agent1.get_state()

        repo.save_agent_state(
            session_id=session.id,
            agent_state=state_json,
            conversation_history=history_json,
            current_state=current_state,
        )

        # Retrieve session
        restored_session = repo.get_session(session.id)

        # Create new agent and restore from session
        flow2 = Flow(name="test2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)

        if restored_session.agent_state:
            agent2.restore_state(restored_session.agent_state)

        # States should match
        assert agent2.get_state() == current_state

    def test_conversation_continues_after_restore(self):
        """Test that conversation can continue after restoration"""
        repo = SessionRepository()

        # Create session
        session = repo.create_session(user_id="test-user")

        # First agent - start conversation
        flow1 = Flow(name="test1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)
        agent1.chat("Hi")
        agent1.chat("1")  # Select grade

        # Save state
        repo.save_agent_state(
            session_id=session.id,
            agent_state=agent1.serialize_state(),
            conversation_history=json.dumps(agent1.get_conversation_history()),
            current_state=agent1.get_state(),
        )

        # Restore in new agent
        restored_session = repo.get_session(session.id)
        flow2 = Flow(name="test2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)
        agent2.restore_state(restored_session.agent_state)

        # Continue conversation
        response = agent2.chat("1")  # Select strand

        # Should get a valid response
        assert response is not None
        assert isinstance(response, str)


class TestConversationHistory:
    """Test conversation history persistence"""

    def test_history_preserved_across_sessions(self):
        """Test that conversation history is preserved"""
        repo = SessionRepository()
        session = repo.create_session(user_id="test-user")

        # Create agent and have conversation
        flow1 = Flow(name="test1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)

        messages = ["Hi", "1", "1"]
        for msg in messages:
            agent1.chat(msg)

        history1 = agent1.get_conversation_history()

        # Save and restore
        repo.save_agent_state(
            session_id=session.id,
            agent_state=agent1.serialize_state(),
            conversation_history=json.dumps(history1),
            current_state=agent1.get_state(),
        )

        restored_session = repo.get_session(session.id)
        flow2 = Flow(name="test2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)
        agent2.restore_state(restored_session.agent_state)

        history2 = agent2.get_conversation_history()

        # Histories should match (at least in length)
        assert len(history2) == len(history1)

    def test_empty_history_on_new_session(self):
        """Test that new sessions start with empty history"""
        repo = SessionRepository()
        session = repo.create_session(user_id="test-user")

        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # New agent should have empty or minimal history
        history = agent.get_conversation_history()
        assert len(history) == 0


class TestErrorHandling:
    """Test error handling in persistence"""

    def test_restore_invalid_json(self):
        """Test handling of invalid JSON during restore"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Should handle invalid JSON gracefully
        with pytest.raises((json.JSONDecodeError, Exception)):
            agent.restore_state("invalid json")

    def test_restore_with_missing_fields(self):
        """Test handling of JSON with missing required fields"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Minimal JSON that might be missing fields
        minimal_state = json.dumps(
            {
                "current_state": "welcome",
                "lesson_requirements": {},
                "conversation_history": [],
            }
        )

        # Should not crash
        try:
            agent.restore_state(minimal_state)
            # If it succeeds, verify it's in a reasonable state
            assert agent.get_state() == "welcome"
        except Exception as e:
            # If it fails, it should fail gracefully
            pytest.fail(f"Restore should handle minimal JSON: {e}")
