#!/usr/bin/env python3
"""Test the draft ID generation fix to ensure no duplicates after pruning"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.draft_history import DraftHistoryManager

def test_draft_id_after_pruning():
    """Test that draft IDs remain unique even after pruning"""
    
    print("=" * 60)
    print("TESTING DRAFT ID GENERATION AFTER PRUNING")
    print("=" * 60)
    
    try:
        # Create draft manager
        draft_manager = DraftHistoryManager()
        
        print(f"✅ Session ID: {draft_manager.session_id}")
        
        # Create original draft
        print("\n📝 Creating original draft...")
        draft_manager.create_draft(
            content="Original lesson content",
            grade_level="Kindergarten",
            strand_code="CN",
            strand_name="Connect",
            standard_id="K.CN.1",
            objectives_count=3,
            is_original=True
        )
        
        # Create many drafts to trigger pruning
        print("\n📝 Creating 15 drafts to trigger pruning...")
        created_draft_ids = []
        
        for i in range(1, 16):  # Create 15 edited drafts
            draft = draft_manager.create_draft(
                content=f"Edited lesson content {i}",
                grade_level="Kindergarten",
                strand_code="CN",
                strand_name="Connect",
                standard_id="K.CN.1",
                objectives_count=3,
                is_original=False
            )
            created_draft_ids.append(draft.draft_id)
            print(f"   Created: {draft.draft_id}")
        
        # Check that all created draft IDs are unique
        print(f"\n🔍 Checking for duplicate draft IDs...")
        unique_ids = set(created_draft_ids)
        if len(unique_ids) == len(created_draft_ids):
            print("✅ No duplicate draft IDs found")
        else:
            print("❌ DUPLICATE DRAFT IDS DETECTED!")
            duplicates = [id for id in created_draft_ids if created_draft_ids.count(id) > 1]
            print(f"   Duplicates: {set(duplicates)}")
            return False
        
        # Check final state
        final_drafts = draft_manager.list_drafts()
        final_draft_ids = [d.draft_id for d in final_drafts]
        
        print(f"\n📊 Final state:")
        print(f"   Total drafts created: {len(created_draft_ids)}")
        print(f"   Final drafts in memory: {len(final_drafts)}")
        print(f"   Max drafts allowed: {draft_manager.max_drafts}")
        
        # Verify original is preserved
        if "original" in final_draft_ids:
            print("✅ Original draft preserved")
        else:
            print("❌ Original draft missing!")
            return False
        
        # Verify no duplicates in final state
        if len(set(final_draft_ids)) == len(final_draft_ids):
            print("✅ No duplicates in final draft list")
        else:
            print("❌ Duplicates in final draft list!")
            return False
        
        # Test counter persistence by creating more drafts
        print(f"\n🔄 Testing counter persistence after pruning...")
        last_counter = draft_manager._draft_counter
        
        new_draft = draft_manager.create_draft(
            content="New draft after pruning",
            grade_level="Kindergarten",
            strand_code="CN",
            strand_name="Connect",
            standard_id="K.CN.1",
            objectives_count=3,
            is_original=False
        )
        
        expected_id = f"draft_{last_counter + 1}"
        if new_draft.draft_id == expected_id:
            print(f"✅ Counter persisted correctly: {new_draft.draft_id}")
        else:
            print(f"❌ Counter reset! Expected {expected_id}, got {new_draft.draft_id}")
            return False
        
        # Cleanup
        draft_manager.cleanup_workspace()
        
        print(f"\n🎯 Draft ID generation fix working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Draft ID fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_draft_id_after_pruning()
    
    if success:
        print("\n🎉 Draft ID generation fix verified!")
    else:
        print("\n❌ Draft ID generation fix test failed")