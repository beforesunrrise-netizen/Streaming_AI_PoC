"""
Simple memory-based TTL cache manager
"""

import time
from typing import Any, Optional, Dict, Tuple
import hashlib
import json


class CacheManager:
    """
    Simple in-memory cache with TTL (Time To Live)
    """

    def __init__(self):
        # Cache structure: {key: (value, expire_time)}
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def _make_key(self, url: str, params: Optional[dict] = None) -> str:
        """
        Create cache key from URL and parameters
        Args:
            url: Request URL
            params: Request parameters (optional)
        Returns:
            Cache key (hash string)
        """
        key_data = url
        if params:
            # Sort params for consistent hashing
            key_data += json.dumps(params, sort_keys=True)

        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, url: str, params: Optional[dict] = None) -> Optional[Any]:
        """
        Get value from cache if not expired
        Args:
            url: Request URL
            params: Request parameters (optional)
        Returns:
            Cached value or None if not found/expired
        """
        key = self._make_key(url, params)

        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]

        # Check if expired
        if time.time() > expire_time:
            del self._cache[key]
            return None

        return value

    def set(self, url: str, value: Any, ttl: int = 60, params: Optional[dict] = None):
        """
        Set value in cache with TTL
        Args:
            url: Request URL
            value: Value to cache
            ttl: Time to live in seconds (default: 60)
            params: Request parameters (optional)
        """
        key = self._make_key(url, params)
        expire_time = time.time() + ttl
        self._cache[key] = (value, expire_time)

    def clear(self):
        """
        Clear all cache
        """
        self._cache.clear()

    def clean_expired(self):
        """
        Remove all expired entries
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time > expire_time
        ]

        for key in expired_keys:
            del self._cache[key]


# Global cache instance
_cache_instance = CacheManager()


def get_cache() -> CacheManager:
    """
    Get global cache instance
    Returns:
        CacheManager instance
    """
    return _cache_instance
