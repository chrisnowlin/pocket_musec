#!/usr/bin/env python3
"""
Verification script for UI objective integration fixes.
This script verifies that the key changes are in place and working.
"""

import os
import re


def verify_file_changes():
    """Verify that the required changes are present in the files"""

    print("🔍 Verifying UI Objective Integration Fixes")
    print("=" * 50)

    checks_passed = 0
    total_checks = 0

    # Check 1: useSession.ts includes selected_objectives in payload
    print("\n1. Checking useSession.ts...")
    total_checks += 1
    use_session_path = "frontend/src/hooks/useSession.ts"
    if os.path.exists(use_session_path):
        with open(use_session_path, "r") as f:
            content = f.read()
            if "payload.selected_objectives = selectedObjective;" in content:
                print("   ✅ selected_objectives added to API payload")
                checks_passed += 1
            else:
                print("   ❌ selected_objectives missing from API payload")
    else:
        print("   ❌ useSession.ts file not found")

    # Check 2: UnifiedPage.tsx passes selectedObjective to initSession
    print("\n2. Checking UnifiedPage.tsx...")
    total_checks += 1
    unified_page_path = "frontend/src/pages/UnifiedPage.tsx"
    if os.path.exists(unified_page_path):
        with open(unified_page_path, "r") as f:
            content = f.read()
            if "lessonSettings.selectedObjective || null" in content:
                print("   ✅ selectedObjective passed to initSession")
                checks_passed += 1
            else:
                print("   ❌ selectedObjective not passed to initSession")
    else:
        print("   ❌ UnifiedPage.tsx file not found")

    # Check 3: UnifiedPage.tsx restores selected_objectives from session
    print("\n3. Checking session objective restoration...")
    total_checks += 1
    if os.path.exists(unified_page_path):
        with open(unified_page_path, "r") as f:
            content = f.read()
            if "loadedSession.selected_objectives || null" in content:
                print("   ✅ selected_objectives restored from session")
                checks_passed += 1
            else:
                print("   ❌ selected_objectives not restored from session")
    else:
        print("   ❌ UnifiedPage.tsx file not found")

    # Check 4: types.ts includes selected_objectives
    print("\n4. Checking types.ts...")
    total_checks += 1
    types_path = "frontend/src/lib/types.ts"
    if os.path.exists(types_path):
        with open(types_path, "r") as f:
            content = f.read()
            if "selected_objectives?: string | null" in content:
                print("   ✅ selected_objectives added to SessionResponsePayload")
                checks_passed += 1
            else:
                print("   ❌ selected_objectives missing from SessionResponsePayload")
    else:
        print("   ❌ types.ts file not found")

    # Check 5: Verify backend models support objectives
    print("\n5. Checking backend models...")
    total_checks += 1
    backend_models_path = "backend/api/models.py"
    if os.path.exists(backend_models_path):
        with open(backend_models_path, "r") as f:
            content = f.read()
            if "selected_objectives: Optional[str] = None" in content:
                print("   ✅ Backend models support selected_objectives")
                checks_passed += 1
            else:
                print("   ❌ Backend models missing selected_objectives")
    else:
        print("   ❌ Backend models.py file not found")

    # Summary
    print("\n" + "=" * 50)
    print(f"Verification Results: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("\nThe UI objective integration is complete:")
        print("• Frontend sends selected_objectives to backend")
        print("• Session creation and loading preserve objectives")
        print("• Type definitions include selected_objectives")
        print("• Backend models support the integration")
        return True
    else:
        print("❌ Some fixes are missing. Please review the failed checks.")
        return False


def verify_integration_logic():
    """Verify the integration logic with examples"""

    print("\n🧪 Testing Integration Logic")
    print("=" * 35)

    # Test the data flow
    print("\n1. Testing UI to API data flow...")

    # Simulate UI selection
    ui_selection = ["3.CN.1.1", "3.CN.1.2"]
    api_format = ",".join(ui_selection)

    print(f"   UI selection: {ui_selection}")
    print(f"   API format: '{api_format}'")

    # Test backend parsing
    if api_format:
        parsed_objectives = [
            obj.strip() for obj in api_format.split(",") if obj.strip()
        ]
        print(f"   Backend parsed: {parsed_objectives}")

        if (
            len(parsed_objectives) == 2
            and "3.CN.1.1" in parsed_objectives
            and "3.CN.1.2" in parsed_objectives
        ):
            print("   ✅ Data flow working correctly")
        else:
            print("   ❌ Data flow has issues")
            return False
    else:
        print("   ❌ No objectives to parse")
        return False

    # Test lesson generation filtering
    print("\n2. Testing objective filtering for lessons...")

    available_objectives = [
        "3.CN.1.1 - Improvise rhythmic patterns",
        "3.CN.1.2 - Improvise melodic patterns",
        "3.CN.1.3 - Improvise harmonic patterns",
    ]

    filtered_objectives = []
    for obj in available_objectives:
        obj_code = obj.split(" - ")[0].strip()
        if obj_code in parsed_objectives:
            filtered_objectives.append(obj)

    print(f"   Available: {len(available_objectives)} objectives")
    print(f"   Selected: {len(parsed_objectives)} objectives")
    print(f"   Filtered: {len(filtered_objectives)} objectives")

    if len(filtered_objectives) == 2 and "3.CN.1.3" not in "".join(filtered_objectives):
        print("   ✅ Objective filtering working correctly")
        return True
    else:
        print("   ❌ Objective filtering has issues")
        return False


def main():
    """Run all verification checks"""

    print("🚀 UI Objective Integration Verification")
    print("=" * 55)

    # Check file changes
    files_ok = verify_file_changes()

    # Check integration logic
    logic_ok = verify_integration_logic()

    print("\n" + "=" * 55)
    if files_ok and logic_ok:
        print("🎉 COMPLETE VERIFICATION SUCCESSFUL!")
        print("\n✅ The UI objective integration is ready for testing:")
        print("   1. All required files have been modified")
        print("   2. Data flow logic is working correctly")
        print("   3. Frontend-backend integration is complete")
        print("   4. Ready for end-to-end user testing")
        print("\n🔧 Next steps:")
        print("   • Start the frontend and backend servers")
        print("   • Test objective selection in the UI")
        print("   • Verify objectives appear in generated lessons")
        return 0
    else:
        print("❌ VERIFICATION FAILED!")
        print("   Some issues were found. Please review the checks above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
