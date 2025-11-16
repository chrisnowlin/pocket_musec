# Standard Serialization Fix

## Issue

The application was experiencing a 500 Internal Server Error when sending chat messages after selecting a standard. The error was:

```
TypeError: Object of type Standard is not JSON serializable
```

This occurred because the `Standard` database model object was being stored directly in the agent's `lesson_requirements` dictionary, which later failed when trying to serialize the agent state to JSON.

## Root Cause

In `backend/api/routes/sessions.py`, the `_create_lesson_agent` function was loading the Standard object from the database and storing it directly in the agent's state:

```python
if session.selected_standards:
    standard = standard_repo.get_standard_by_id(session.selected_standards)
    if standard:
        agent.lesson_requirements["standard"] = standard  # ← Database model object!
```

When the agent state was later serialized to save to the session, this caused a JSON serialization error because SQLAlchemy model objects cannot be directly serialized to JSON.

## Fix

The fix involved three changes:

### 1. Serialize Standard on Agent Creation (`backend/api/routes/sessions.py`)

When creating the lesson agent and pre-populating it with session context, convert the Standard object to a serializable dictionary:

```python
if session.selected_standards:
    standard = standard_repo.get_standard_by_id(session.selected_standards)
    if standard:
        # Ensure standard is a serializable dictionary, not a model object
        agent.lesson_requirements["standard"] = _standard_to_response(
            standard, standard_repo
        ).model_dump()
```

### 2. Serialize Standard on State Restoration (`backend/api/routes/sessions.py`)

When restoring agent state from a session, check if the standard is already serialized. If not, convert it:

```python
# Ensure standard object is serializable if present
if "standard" in agent.lesson_requirements and not isinstance(
    agent.lesson_requirements["standard"], (dict, type(None))
):
    standard = agent.lesson_requirements["standard"]
    standard_repo = StandardsRepository()
    agent.lesson_requirements["standard"] = _standard_to_response(
        standard, standard_repo
    ).model_dump()
```

### 3. Handle Both Formats in `_compose_lesson_from_agent` (`backend/api/routes/sessions.py`)

Since the standard can now be either a dict (serialized) or an object (legacy), handle both formats:

```python
standard = requirements.get("standard")
# Handle both dict (serialized) and object formats
if isinstance(standard, dict):
    standard_label = standard.get("id", "Selected standard")
    standard_id = standard.get("id")
    standard_file_id = standard.get("file_id")
else:
    standard_label = standard.standard_id if standard else "Selected standard"
    standard_id = standard.standard_id if standard else None
    standard_file_id = standard.file_id if (standard and hasattr(standard, "file_id")) else None
```

### 4. Handle Both Formats in `serialize_state` (`backend/pocketflow/lesson_agent.py`)

Update the agent's `serialize_state` method to handle pre-serialized standard dicts:

```python
if key == "standard":
    # Serialize standard object or pass through if already a dict
    if value:
        if isinstance(value, dict):
            # Already serialized
            serializable_reqs[key] = value
        else:
            # Serialize standard object
            serializable_reqs[key] = {
                "standard_id": value.standard_id,
                "grade_level": value.grade_level,
                ...
            }
```

## Testing

Created `test_serialization_fix.py` to verify:

1. ✓ Standard is loaded from database
2. ✓ Standard is converted to a dictionary (serialized)
3. ✓ Agent state can be serialized to JSON without errors
4. ✓ Serialized state contains the standard as a dictionary

Test output:
```
Testing Standard serialization fix...

1. Creating test session...
   ✓ Session created: test-serial-87828796

2. Creating lesson agent...
   Session selected_standards: 1.CN.1
   ✓ Standard found: 1.CN.1
   ✓ Agent created successfully

3. Checking standard serialization...
   ✓ Standard is a dict (serialized)
     Keys: ['id', 'code', 'grade', 'strand_code', 'strand_name', 'title', 'description', 'objectives', 'learning_objectives', 'last_used']

4. Testing agent state serialization...
   ✓ Agent state serialized successfully
   ✓ Standard in serialized state is a dict

5. Cleaning up...
   ✓ Test session deleted

✓ TEST PASSED: Standard serialization works correctly!
```

## Impact

This fix ensures that:
- Chat messages can be sent successfully after selecting a standard
- Agent state can be persisted to the database without serialization errors
- The system gracefully handles both legacy (object) and new (dict) standard formats
- All standard-related features continue to work as expected

## Files Modified

1. `backend/api/routes/sessions.py` (3 changes)
   - `_create_lesson_agent`: Serialize standard when pre-populating from session
   - `_create_lesson_agent`: Serialize standard when restoring state
   - `_compose_lesson_from_agent`: Handle both dict and object formats

2. `backend/pocketflow/lesson_agent.py` (1 change)
   - `serialize_state`: Handle pre-serialized standard dicts
