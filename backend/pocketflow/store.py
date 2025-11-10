"""Store component for PocketFlow framework"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime


class Store:
    """Maintains conversation context"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key with optional default"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        old_value = self._data.get(key)
        self._data[key] = value
        
        # Track changes in history
        self._history.append({
            "key": key,
            "old_value": old_value,
            "new_value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    def delete(self, key: str) -> bool:
        """Delete a key, returns True if key existed"""
        if key in self._data:
            old_value = self._data.pop(key)
            self._history.append({
                "key": key,
                "old_value": old_value,
                "new_value": None,
                "timestamp": datetime.now().isoformat(),
                "deleted": True
            })
            return True
        return False
    
    def keys(self) -> List[str]:
        """Get all keys"""
        return list(self._data.keys())
    
    def clear(self) -> None:
        """Clear all data"""
        self._data.clear()
        self._history.clear()
    
    def get_history(self, key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get change history, optionally filtered by key"""
        if key is None:
            return self._history.copy()
        return [h for h in self._history if h["key"] == key]
    
    def to_dict(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return self._data.copy()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def __repr__(self) -> str:
        return f"Store(keys={len(self._data)}, history={len(self._history)})"