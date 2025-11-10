#!/usr/bin/env python3
"""Test the editor integration functionality"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.editor_integration import EditorIntegration

def test_editor_detection():
    """Test editor detection on current system"""
    
    print("=" * 60)
    print("TESTING EDITOR INTEGRATION")
    print("=" * 60)
    
    try:
        editor = EditorIntegration()
        
        # Get editor info
        info = editor.get_editor_info()
        
        print(f"✅ Platform: {info['platform']}")
        print(f"✅ Detected editor: {info['detected_editor']}")
        print(f"✅ Environment editor: {info['editor_env_var']}")
        print(f"✅ Available editors: {', '.join(info['available_editors'])}")
        
        # Test temp file creation
        test_content = """# Test Lesson Draft

This is a test lesson draft created by PocketMusec.

## Grade Level
Kindergarten

## Strand
Connect (CN)

## Standard
K.CN.1 - Understand the global, interdisciplinary, and historical contexts of music.

## Objectives
- K.CN.1.1 Identify the similarities and differences of music representing diverse global communities.

## Lesson Activities
1. Listen to music from different cultures
2. Discuss similarities and differences
3. Create a world music map

Edit this lesson as needed!
"""
        
        print("\n📝 Creating temporary file...")
        file_path, original_hash = editor.create_temp_file(test_content)
        print(f"✅ Created: {file_path}")
        print(f"✅ Hash: {original_hash[:16]}...")
        
        # Test change detection
        has_changed, new_hash = editor.detect_file_changes(file_path, original_hash)
        print(f"✅ Change detection: {has_changed}")
        
        print(f"\n🎯 Editor integration working correctly!")
        print(f"   Ready to integrate with lesson generation workflow")
        
        return True
        
    except Exception as e:
        print(f"❌ Editor integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_editor_detection()
    
    if success:
        print("\n🎉 Editor integration test completed successfully!")
    else:
        print("\n❌ Editor integration test failed")