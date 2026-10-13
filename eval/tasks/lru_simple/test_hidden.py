import pytest
from lru_simple import LRUCache
def test_eviction(): c = LRUCache(2); c.put("a", 1); c.put("b", 2); assert c.get("a") == 1; c.put("c", 3); assert c.get("b") is None; assert c.get("a") == 1; assert c.get("c") == 3
def test_update_existing(): c = LRUCache(1); c.put("a", 1); c.put("a", 2); assert c.get("a") == 2
def test_bad_capacity(): pytest.raises(ValueError, LRUCache, 0)
