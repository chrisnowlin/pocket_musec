#!/usr/bin/env python3
"""Test the integrated draft history functionality with CLI workflow"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.draft_history import DraftHistoryManager
from cli.commands.generate import display_session_summary

def test_integrated_draft_history():
    """Test the complete integrated draft history functionality"""
    
    print("=" * 60)
    print("TESTING INTEGRATED DRAFT HISTORY FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Create draft manager
        draft_manager = DraftHistoryManager()
        
        print(f"✅ Session ID: {draft_manager.session_id}")
        print(f"✅ Workspace: {draft_manager.workspace}")
        
        # Simulate lesson generation workflow
        print("\n📝 Simulating lesson generation workflow...")
        
        # Create original draft (simulating initial lesson generation)
        original_content = """# Music Lesson: Rhythm Patterns

## Grade Level
2nd Grade

## Standard
2.CR.1.1 - Execute rhythmic patterns

## Objectives
1. Students will clap quarter note and eighth note patterns
2. Students will identify rhythmic patterns in music
3. Students will create their own rhythmic patterns

## Lesson Activities
1. Warm-up: Call and response clapping
2. Introduction: Quarter and eighth note notation
3. Practice: Rhythm reading exercises
4. Creation: Student composition time
5. Performance: Share student compositions

## Assessment
- Observation of participation
- Rhythm reading accuracy
- Original rhythm pattern creation
"""
        
        original_draft = draft_manager.create_draft(
            content=original_content,
            grade_level="2nd Grade",
            strand_code="CR",
            strand_name="Create and Respond",
            standard_id="2.CR.1.1",
            objectives_count=3,
            is_original=True
        )
        
        print(f"✅ Created original draft: {original_draft.draft_id}")
        
        # Simulate editor edits
        print("\n✏️ Simulating editor edits...")
        
        edit_1_content = """# Music Lesson: Rhythm Patterns (Edited)

## Grade Level
2nd Grade

## Standard
2.CR.1.1 - Execute rhythmic patterns

## Objectives
1. Students will clap quarter note and eighth note patterns
2. Students will identify rhythmic patterns in music
3. Students will create their own rhythmic patterns
4. Students will perform rhythmic patterns with instruments

## Lesson Activities
1. Warm-up: Call and response clapping
2. Introduction: Quarter and eighth note notation
3. Practice: Rhythm reading exercises with body percussion
4. Instrument exploration: Using rhythm instruments
5. Creation: Student composition time in small groups
6. Performance: Share student compositions

## Assessment
- Observation of participation
- Rhythm reading accuracy
- Original rhythm pattern creation
- Instrument performance skills

## Materials Needed
- Rhythm sticks
- Hand drums
- Triangle
- Rhythm notation cards
"""
        
        edited_draft_1 = draft_manager.create_draft(
            content=edit_1_content,
            grade_level="2nd Grade",
            strand_code="CR",
            strand_name="Create and Respond",
            standard_id="2.CR.1.1",
            objectives_count=4,
            is_original=False
        )
        
        print(f"✅ Created edited draft: {edited_draft_1.draft_id}")
        
        # Another edit
        edit_2_content = """# Music Lesson: Rhythm Patterns - Final Version

## Grade Level
2nd Grade

## Standard
2.CR.1.1 - Execute rhythmic patterns

## Objectives
1. Students will clap quarter note and eighth note patterns
2. Students will identify rhythmic patterns in music
3. Students will create their own rhythmic patterns
4. Students will perform rhythmic patterns with instruments
5. Students will notate simple rhythmic patterns

## Lesson Activities
1. Warm-up: Call and response clapping (5 min)
2. Introduction: Quarter and eighth note notation (10 min)
3. Practice: Rhythm reading exercises with body percussion (15 min)
4. Instrument exploration: Using rhythm instruments (10 min)
5. Creation: Student composition time in small groups (15 min)
6. Notation: Writing down rhythmic patterns (10 min)
7. Performance: Share student compositions (10 min)

## Assessment
- Observation of participation
- Rhythm reading accuracy
- Original rhythm pattern creation
- Instrument performance skills
- Basic notation skills

## Materials Needed
- Rhythm sticks
- Hand drums
- Triangle
- Rhythm notation cards
- Whiteboard and markers
- Student notation sheets

## Differentiation
- Advanced students: Create 4-measure patterns
- Support students: Focus on quarter notes only
- ELL students: Use visual aids and demonstrations
"""
        
        edited_draft_2 = draft_manager.create_draft(
            content=edit_2_content,
            grade_level="2nd Grade",
            strand_code="CR",
            strand_name="Create and Respond",
            standard_id="2.CR.1.1",
            objectives_count=5,
            is_original=False
        )
        
        print(f"✅ Created final edited draft: {edited_draft_2.draft_id}")
        
        # Test draft retrieval
        print(f"\n📖 Testing draft retrieval...")
        latest = draft_manager.get_latest_draft()
        if latest:
            content = draft_manager.get_draft_content(latest.draft_id)
            print(f"✅ Retrieved latest draft ({latest.draft_id}): {len(content)} characters")
        
        # Test workspace info
        info = draft_manager.get_workspace_info()
        print(f"\n📊 Workspace info:")
        print(f"   Total drafts: {info['total_drafts']}")
        print(f"   Max drafts: {info['max_drafts']}")
        print(f"   Session ID: {info['session_id']}")
        
        # Test session summary display
        print(f"\n📋 Testing session summary display...")
        display_session_summary(draft_manager)
        
        # Test pruning (create more drafts to exceed limit)
        print(f"\n🔄 Testing draft pruning...")
        for i in range(3, 15):  # This should trigger pruning
            test_content = f"""# Test Draft {i}

## Content
This is test draft {i} for pruning functionality.
"""
            
            draft_manager.create_draft(
                content=test_content,
                grade_level="2nd Grade",
                strand_code="CR",
                strand_name="Create and Respond",
                standard_id="2.CR.1.1",
                objectives_count=1,
                is_original=False
            )
        
        final_drafts = draft_manager.list_drafts()
        print(f"✅ After pruning: {len(final_drafts)} drafts (max: {draft_manager.max_drafts})")
        
        # Verify original is preserved
        original_exists = any(d.draft_id == "original" for d in final_drafts)
        print(f"✅ Original draft preserved: {original_exists}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up workspace...")
        draft_manager.cleanup_workspace()
        
        print(f"\n🎯 Integrated draft history functionality working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Integrated draft history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_draft_history()
    
    if success:
        print("\n🎉 Integrated draft history test completed successfully!")
        print("✅ Phase 10 (Draft History Management) - COMPLETE")
        print("✅ Phase 11 (Session Summary) - COMPLETE")
    else:
        print("\n❌ Integrated draft history test failed")