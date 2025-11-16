#!/usr/bin/env python3
"""
Debug test to isolate the API issue
"""

import sys
import os

sys.path.append(os.getcwd())

from backend.api.routes.sessions import _session_to_response
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.session_repository import SessionRepository
from backend.auth.models import Session


def test_session_conversion():
    """Test the session to response conversion"""

    print("Testing session to response conversion...")

    # Create a test session
    repo = SessionRepository()
    session = repo.create_session(
        user_id="test-user",
        grade_level="Grade 3",
        strand_code="Connect",
        standard_id="3.CN.1",
        additional_standards="3.CN.2,3.CN.3",
        additional_objectives="3.CN.2.1,3.CN.3.1",
    )

    print(f"✓ Session created: {session.id}")
    print(f"  Additional standards: {session.additional_standards}")
    print(f"  Additional objectives: {session.additional_objectives}")

    # Test conversion
    try:
        standard_repo = StandardsRepository()
        response = _session_to_response(session, standard_repo)

        print(f"✓ Conversion successful")
        print(f"  Additional standards type: {type(response.additional_standards)}")
        print(f"  Additional objectives type: {type(response.additional_objectives)}")

        if response.additional_standards:
            print(f"  Standards count: {len(response.additional_standards)}")
            for standard in response.additional_standards:
                print(
                    f"    - {standard.get('code')}: {standard.get('description', '')[:30]}..."
                )

        if response.additional_objectives:
            print(f"  Objectives: {response.additional_objectives}")

    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_session_conversion()
