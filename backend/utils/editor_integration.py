"""Editor integration for lesson draft editing"""

import os
import sys
import subprocess
import tempfile
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class EditorIntegration:
    """Handle system editor detection and file editing for lesson drafts"""
    
    def __init__(self):
        self.detected_editor = self._detect_system_editor()
    
    def _detect_system_editor(self) -> str:
        """
        Detect the system default editor based on platform and environment
        Returns a command that can be used to launch the editor
        """
        # Check environment variables first
        editor_vars = ['EDITOR', 'VISUAL']
        for var in editor_vars:
            editor = os.environ.get(var)
            if editor:
                if self._verify_editor_available(editor):
                    logger.info(f"Using editor from {var}: {editor}")
                    return editor
                else:
                    logger.warning(f"Editor {editor} from {var} not available")
        
        # Platform-specific defaults
        if sys.platform.startswith('win'):
            # Windows defaults
            windows_editors = ['code', 'notepad++', 'notepad', 'nano']
            for editor in windows_editors:
                if self._verify_editor_available(editor):
                    logger.info(f"Using Windows editor: {editor}")
                    return editor
                    
        elif sys.platform.startswith('darwin'):
            # macOS defaults
            macos_editors = ['code', 'nano', 'vim', 'vi']
            for editor in macos_editors:
                if self._verify_editor_available(editor):
                    logger.info(f"Using macOS editor: {editor}")
                    return editor
                    
        else:
            # Linux/Unix defaults
            linux_editors = ['code', 'nano', 'vim', 'vi', 'emacs']
            for editor in linux_editors:
                if self._verify_editor_available(editor):
                    logger.info(f"Using Linux editor: {editor}")
                    return editor
        
        # Fallback to nano if available, otherwise vi
        fallback_editors = ['nano', 'vi']
        for editor in fallback_editors:
            if self._verify_editor_available(editor):
                logger.warning(f"Using fallback editor: {editor}")
                return editor
        
        # No editor found
        raise RuntimeError("No suitable text editor found. Please set EDITOR environment variable.")
    
    def _verify_editor_available(self, editor: str) -> bool:
        """Verify that an editor command is available on the system"""
        try:
            # Handle editor commands with arguments (e.g., "code --wait")
            editor_cmd = editor.split()[0]
            
            # Use 'which' on Unix-like systems, 'where' on Windows
            if sys.platform.startswith('win'):
                result = subprocess.run(['where', editor_cmd], 
                                      capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['which', editor_cmd], 
                                      capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_available_editors(self) -> List[str]:
        """Get a list of available editors on the system"""
        all_editors = []
        
        # Common editors by platform
        if sys.platform.startswith('win'):
            all_editors.extend(['code', 'notepad++', 'notepad', 'nano'])
        elif sys.platform.startswith('darwin'):
            all_editors.extend(['code', 'nano', 'vim', 'vi', 'emacs'])
        else:
            all_editors.extend(['code', 'nano', 'vim', 'vi', 'emacs'])
        
        # Filter to only available editors
        available = [editor for editor in all_editors if self._verify_editor_available(editor)]
        
        # Add environment editor if set and not in list
        env_editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
        if env_editor and env_editor not in available:
            if self._verify_editor_available(env_editor):
                available.insert(0, env_editor)
        
        return available
    
    def create_temp_file(self, content: str, suffix: str = ".md") -> Tuple[Path, str]:
        """
        Create a temporary file with the given content
        
        Args:
            content: Content to write to the file
            suffix: File suffix (extension)
            
        Returns:
            Tuple of (file_path, file_hash)
        """
        # Create temp file in user's temp directory with predictable name
        temp_dir = Path(tempfile.gettempdir()) / "pocketmusec"
        temp_dir.mkdir(exist_ok=True)
        
        # Create file with timestamp and UID for uniqueness
        import time
        timestamp = int(time.time() * 1000)
        unique_suffix = uuid.uuid4().hex[:8]
        file_name = f"lesson_draft_{timestamp}_{unique_suffix}{suffix}"
        file_path = temp_dir / file_name
        
        # Write content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Calculate hash for change detection
        file_hash = self._calculate_file_hash(file_path)
        
        logger.info(f"Created temp file: {file_path}")
        return file_path, file_hash
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for change detection"""
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    
    def launch_editor(self, file_path: Path, editor: Optional[str] = None) -> bool:
        """
        Launch the system editor with the given file
        
        Args:
            file_path: Path to the file to edit
            editor: Editor command to use (defaults to detected editor)
            
        Returns:
            True if editor launched successfully, False otherwise
        """
        editor_cmd = editor or self.detected_editor
        
        try:
            # Special handling for VS Code to make it wait
            if 'code' in editor_cmd:
                # Ensure --wait flag for VS Code
                if '--wait' not in editor_cmd:
                    editor_cmd = f"{editor_cmd} --wait"
            
            # Launch editor
            logger.info(f"Launching editor: {editor_cmd} {file_path}")
            
            # Build command list
            if ' ' in editor_cmd:
                # Editor command with arguments (like "code --wait")
                cmd_parts = editor_cmd.split() + [str(file_path)]
            else:
                # Simple editor command
                cmd_parts = [editor_cmd, str(file_path)]
            
            # Use subprocess.run to wait for editor to close
            result = subprocess.run(
                cmd_parts,
                capture_output=False,
                text=True
            )
            
            # For many editors, non-zero exit code doesn't mean failure
            # (e.g., nano exits with 1 on Ctrl+X without saving)
            return True
            
        except KeyboardInterrupt:
            logger.info("Editor interrupted by user")
            return True
        except Exception as e:
            logger.error(f"Failed to launch editor: {e}")
            return False
    
    def detect_file_changes(self, file_path: Path, original_hash: str) -> Tuple[bool, str]:
        """
        Detect if a file has changed since original hash was calculated
        
        Args:
            file_path: Path to the file to check
            original_hash: Original hash of the file
            
        Returns:
            Tuple of (has_changed, new_hash)
        """
        if not file_path.exists():
            return False, original_hash
        
        new_hash = self._calculate_file_hash(file_path)
        has_changed = new_hash != original_hash
        
        logger.info(f"File change detection: {has_changed}")
        return has_changed, new_hash
    
    def get_editor_info(self) -> dict:
        """Get information about the detected editor"""
        return {
            'detected_editor': self.detected_editor,
            'available_editors': self.get_available_editors(),
            'platform': sys.platform,
            'editor_env_var': os.environ.get('EDITOR') or os.environ.get('VISUAL')
        }
