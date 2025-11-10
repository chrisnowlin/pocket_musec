"""Tests for PocketFlow Store component"""

def test_store_creation():
    """Test that a Store can be created"""
    from backend.pocketflow.store import Store
    
    store = Store()
    assert store is not None
    assert len(store) == 0


def test_store_set_get():
    """Test setting and getting values"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    
    assert store.get("key1") == "value1"
    assert len(store) == 1


def test_store_get_default():
    """Test getting values with default"""
    from backend.pocketflow.store import Store
    
    store = Store()
    
    assert store.get("nonexistent") is None
    assert store.get("nonexistent", "default") == "default"


def test_store_delete():
    """Test deleting keys"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    
    assert store.delete("key1") is True
    assert store.get("key1") is None
    assert store.delete("nonexistent") is False


def test_store_keys():
    """Test getting all keys"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    store.set("key2", "value2")
    
    keys = store.keys()
    assert set(keys) == {"key1", "key2"}


def test_store_clear():
    """Test clearing all data"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    store.set("key2", "value2")
    
    store.clear()
    assert len(store) == 0
    assert store.keys() == []


def test_store_history():
    """Test that change history is tracked"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    store.set("key1", "value2")
    store.delete("key1")
    
    history = store.get_history()
    assert len(history) == 3
    
    # First set
    assert history[0]["key"] == "key1"
    assert history[0]["old_value"] is None
    assert history[0]["new_value"] == "value1"
    
    # Second set
    assert history[1]["key"] == "key1"
    assert history[1]["old_value"] == "value1"
    assert history[1]["new_value"] == "value2"
    
    # Delete
    assert history[2]["key"] == "key1"
    assert history[2]["old_value"] == "value2"
    assert history[2]["new_value"] is None
    assert history[2]["deleted"] is True


def test_store_history_filter():
    """Test filtering history by key"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    store.set("key2", "value2")
    store.set("key1", "value3")
    
    key1_history = store.get_history("key1")
    assert len(key1_history) == 2
    assert all(h["key"] == "key1" for h in key1_history)


def test_store_contains():
    """Test key membership testing"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    
    assert "key1" in store
    assert "key2" not in store


def test_store_to_dict():
    """Test converting store to dictionary"""
    from backend.pocketflow.store import Store
    
    store = Store()
    store.set("key1", "value1")
    store.set("key2", "value2")
    
    data = store.to_dict()
    assert data == {"key1": "value1", "key2": "value2"}
    
    # Ensure it's a copy
    data["key3"] = "value3"
    assert "key3" not in store


def test_store_repr():
    """Test Store string representation"""
    from backend.pocketflow.store import Store
    
    store = Store()
    assert repr(store) == "Store(keys=0, history=0)"
    
    store.set("key1", "value1")
    assert "keys=1" in repr(store)
    assert "history=1" in repr(store)