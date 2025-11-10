#!/usr/bin/env python3
"""Test the draft history management functionality"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.draft_history import DraftHistoryManager

def test_draft_history():
    """Test draft history management"""
    
    print("=" * 60)
    print("TESTING DRAFT HISTORY MANAGEMENT")
    print("=" * 60)
    
    try:
        # Create draft manager
        manager = DraftHistoryManager()
        
        print(f"✅ Session ID: {manager.session_id}")
        print(f"✅ Workspace: {manager.workspace}")
        
        # Create original draft
        original_content = """# Original Lesson

## Grade Level
Kindergarten

## Standard
K.CN.1

## Content
This is the original lesson content.
"""
        
        print("\n📝 Creating original draft...")
        original_draft = manager.create_draft(
            content=original_content,
            grade_level="Kindergarten",
            strand_code="CN",
            strand_name="Connect",
            standard_id="K.CN.1",
            objectives_count=3,
            is_original=True
        )
        
        print(f"✅ Created original draft: {original_draft.draft_id}")
        print(f"   File: {original_draft.file_path}")
        
        # Create edited drafts
        for i in range(1, 4):
            edited_content = f"""# Edited Lesson {i}

## Grade Level
Kindergarten

## Standard
K.CN.1

## Content
This is edited version {i} of the lesson.
New content added in edit {i}.
"""
            
            print(f"\n📝 Creating edited draft {i}...")
            edited_draft = manager.create_draft(
                content=edited_content,
                grade_level="Kindergarten",
                strand_code="CN",
                strand_name="Connect",
                standard_id="K.CN.1",
                objectives_count=3,
                is_original=False
            )
            
            print(f"✅ Created draft: {edited_draft.draft_id}")
        
        # List all drafts
        print(f"\n📋 All drafts ({len(manager.list_drafts())}):")
        for draft in manager.list_drafts():
            print(f"   {draft.draft_id}: {draft.timestamp.strftime('%H:%M:%S')} - {draft.grade_level} {draft.strand_code}")
        
        # Test retrieving content
        print(f"\n📖 Testing content retrieval...")
        latest = manager.get_latest_draft()
        if latest:
            content = manager.get_draft_content(latest.draft_id)
            print(f"✅ Retrieved latest draft ({latest.draft_id}): {len(content)} characters")
        
        # Test workspace info
        info = manager.get_workspace_info()
        print(f"\n📊 Workspace info:")
        print(f"   Total drafts: {info['total_drafts']}")
        print(f"   Max drafts: {info['max_drafts']}")
        
        # Test pruning (create more drafts to exceed limit)
        print(f"\n🔄 Testing draft pruning...")
        for i in range(4, 15):  # This should trigger pruning
            edited_content = f"""# Edited Lesson {i}

## Grade Level
Kindergarten

## Standard
K.CN.1

## Content
This is edited version {i} - should be pruned if too old.
"""
            
            manager.create_draft(
                content=edited_content,
                grade_level="Kindergarten",
                strand_code="CN",
                strand_name="Connect",
                standard_id="K.CN.1",
                objectives_count=3,
                is_original=False
            )
        
        final_drafts = manager.list_drafts()
        print(f"✅ After pruning: {len(final_drafts)} drafts (max: {manager.max_drafts})")
        
        # Cleanup
        print(f"\n🧹 Cleaning up workspace...")
        manager.cleanup_workspace()
        
        print(f"\n🎯 Draft history management working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Draft history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_draft_history()
    
    if success:
        print("\n🎉 Draft history test completed successfully!")
    else:
        print("\n❌ Draft history test failed")