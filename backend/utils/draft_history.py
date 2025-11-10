"""Draft history management for lesson generation sessions"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DraftMetadata:
    """Metadata for a lesson draft"""
    draft_id: str
    timestamp: datetime
    grade_level: str
    strand_code: str
    strand_name: str
    standard_id: str
    objectives_count: int
    has_edits: bool
    file_path: Path
    session_id: str


class DraftHistoryManager:
    """Manage draft history for lesson generation sessions"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.workspace = self._create_session_workspace()
        self.max_drafts = 10  # Original + 9 latest versions
        self.drafts: List[DraftMetadata] = []
        self._draft_counter = 0  # Counter for generating unique draft IDs
        self._load_existing_drafts()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _create_session_workspace(self) -> Path:
        """Create session workspace in temp directory"""
        temp_dir = Path(tempfile.gettempdir()) / "pocketmusec" / f"session_{self.session_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (temp_dir / "drafts").mkdir(exist_ok=True)
        (temp_dir / "metadata").mkdir(exist_ok=True)
        
        logger.info(f"Created session workspace: {temp_dir}")
        return temp_dir
    
    def _load_existing_drafts(self):
        """Load existing drafts from workspace"""
        metadata_file = self.workspace / "metadata" / "drafts.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                
                # Handle both old format (list) and new format (dict with counter)
                if isinstance(data, list):
                    # Old format - just list of drafts
                    drafts_data = data
                    self._draft_counter = 0
                else:
                    # New format - dict with counter and drafts
                    drafts_data = data.get('drafts', [])
                    self._draft_counter = data.get('draft_counter', 0)
                
                for draft_data in drafts_data:
                    # Convert timestamp back to datetime
                    draft_data['timestamp'] = datetime.fromisoformat(draft_data['timestamp'])
                    draft_data['file_path'] = Path(draft_data['file_path'])
                    
                    metadata = DraftMetadata(**draft_data)
                    
                    # Only load if file still exists
                    if metadata.file_path.exists():
                        self.drafts.append(metadata)
                
                # Sort by timestamp
                self.drafts.sort(key=lambda x: x.timestamp)
                
                # If old format, restore counter from existing drafts
                if isinstance(data, list):
                    for draft in self.drafts:
                        if draft.draft_id != "original" and draft.draft_id.startswith("draft_"):
                            try:
                                draft_num = int(draft.draft_id.split("_")[1])
                                self._draft_counter = max(self._draft_counter, draft_num)
                            except (ValueError, IndexError):
                                pass
                
                logger.info(f"Loaded {len(self.drafts)} existing drafts")
                logger.info(f"Restored draft counter to: {self._draft_counter}")
                
            except Exception as e:
                logger.warning(f"Failed to load existing drafts: {e}")
                self._draft_counter = 0
    
    def _save_drafts_metadata(self):
        """Save drafts metadata to file"""
        metadata_file = self.workspace / "metadata" / "drafts.json"
        
        try:
            data = {
                'draft_counter': self._draft_counter,
                'drafts': []
            }
            
            for draft in self.drafts:
                draft_dict = {
                    'draft_id': draft.draft_id,
                    'timestamp': draft.timestamp.isoformat(),
                    'grade_level': draft.grade_level,
                    'strand_code': draft.strand_code,
                    'strand_name': draft.strand_name,
                    'standard_id': draft.standard_id,
                    'objectives_count': draft.objectives_count,
                    'has_edits': draft.has_edits,
                    'file_path': str(draft.file_path),
                    'session_id': draft.session_id
                }
                data['drafts'].append(draft_dict)
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save drafts metadata: {e}")
    
    def create_draft(
        self,
        content: str,
        grade_level: str,
        strand_code: str,
        strand_name: str,
        standard_id: str,
        objectives_count: int,
        is_original: bool = False
    ) -> DraftMetadata:
        """
        Create a new draft
        
        Args:
            content: Lesson content
            grade_level: Grade level for the lesson
            strand_code: Strand code (CN, CR, PR, RE)
            strand_name: Full strand name
            standard_id: Standard identifier
            objectives_count: Number of objectives
            is_original: Whether this is the original draft
            
        Returns:
            DraftMetadata for the created draft
        """
        # Generate draft ID
        if is_original:
            draft_id = f"original"
        else:
            self._draft_counter += 1
            draft_id = f"draft_{self._draft_counter}"
        
        # Create file path
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{draft_id}_{timestamp_str}.md"
        file_path = self.workspace / "drafts" / filename
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create metadata
        metadata = DraftMetadata(
            draft_id=draft_id,
            timestamp=datetime.now(),
            grade_level=grade_level,
            strand_code=strand_code,
            strand_name=strand_name,
            standard_id=standard_id,
            objectives_count=objectives_count,
            has_edits=not is_original,
            file_path=file_path,
            session_id=self.session_id
        )
        
        # Add to drafts list
        self.drafts.append(metadata)
        
        # Prune old drafts if needed
        self._prune_old_drafts()
        
        # Save metadata
        self._save_drafts_metadata()
        
        logger.info(f"Created draft: {draft_id} at {file_path}")
        return metadata
    
    def _prune_old_drafts(self):
        """Remove oldest drafts if we exceed the maximum"""
        if len(self.drafts) <= self.max_drafts:
            return
        
        # Keep original and latest 9 drafts
        original_drafts = [d for d in self.drafts if d.draft_id == "original"]
        other_drafts = [d for d in self.drafts if d.draft_id != "original"]
        
        # Sort by timestamp and keep latest
        other_drafts.sort(key=lambda x: x.timestamp, reverse=True)
        keep_drafts = other_drafts[:9]  # Keep latest 9
        
        # Combine with original
        final_drafts = original_drafts + keep_drafts
        
        # Remove files for drafts being deleted
        draft_ids_to_keep = {d.draft_id for d in final_drafts}
        drafts_to_delete = [d for d in self.drafts if d.draft_id not in draft_ids_to_keep]
        for draft in drafts_to_delete:
            try:
                if draft.file_path.exists():
                    draft.file_path.unlink()
                logger.info(f"Deleted old draft: {draft.draft_id}")
            except Exception as e:
                logger.warning(f"Failed to delete draft file {draft.file_path}: {e}")
        
        self.drafts = final_drafts
    
    def get_draft(self, draft_id: str) -> Optional[DraftMetadata]:
        """Get draft metadata by ID"""
        for draft in self.drafts:
            if draft.draft_id == draft_id:
                return draft
        return None
    
    def get_draft_content(self, draft_id: str) -> Optional[str]:
        """Get draft content by ID"""
        draft = self.get_draft(draft_id)
        if not draft:
            return None
        
        try:
            with open(draft.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read draft {draft_id}: {e}")
            return None
    
    def list_drafts(self) -> List[DraftMetadata]:
        """List all drafts sorted by timestamp"""
        return sorted(self.drafts, key=lambda x: x.timestamp)
    
    def get_latest_draft(self) -> Optional[DraftMetadata]:
        """Get the most recent draft"""
        if not self.drafts:
            return None
        
        return max(self.drafts, key=lambda x: x.timestamp)
    
    def cleanup_workspace(self):
        """Clean up the entire workspace"""
        try:
            if self.workspace.exists():
                shutil.rmtree(self.workspace)
                logger.info(f"Cleaned up workspace: {self.workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {self.workspace}: {e}")
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about the workspace"""
        return {
            'session_id': self.session_id,
            'workspace_path': str(self.workspace),
            'total_drafts': len(self.drafts),
            'max_drafts': self.max_drafts,
            'drafts': [
                {
                    'draft_id': d.draft_id,
                    'timestamp': d.timestamp.isoformat(),
                    'grade_level': d.grade_level,
                    'strand_code': d.strand_code,
                    'standard_id': d.standard_id,
                    'has_edits': d.has_edits
                }
                for d in self.drafts
            ]
        }