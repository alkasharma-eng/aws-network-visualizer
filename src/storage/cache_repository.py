"""
Cache repository using Redis/ElastiCache.

This module provides caching capabilities for frequently accessed
topology data and query results.
"""

import json
import time
from typing import Any, Dict, Optional

from src.core.config import get_settings
from src.core.exceptions import StorageException
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher

logger = get_logger(__name__)


class CacheRepository:
    """
    Repository for caching topology data using Redis.

    Key patterns:
        topology:{region}:{vpc_id}:latest
        analysis:{region}:{vpc_id}:latest
        graph:{region}:{vpc_id}:latest
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache repository.

        Args:
            redis_url: Redis connection URL (defaults to config)
        """
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.elasticache_endpoint
        self.metrics = get_metrics_publisher()
        self.client = None

        if not self.redis_url:
            logger.warning("Redis endpoint not configured, caching disabled")
            return

        try:
            import redis

            self.client = redis.from_url(
                f"redis://{self.redis_url}",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.client.ping()

            logger.info(f"Initialized cache repository: {self.redis_url}")

        except ImportError:
            logger.warning(
                "redis package not installed, caching disabled. "
                "Install with: pip install redis"
            )

        except Exception as e:
            logger.warning(f"Failed to initialize cache: {e}. Caching disabled.")

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (defaults to config)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        ttl = ttl or self.settings.cache_ttl_seconds

        try:
            serialized = json.dumps(value, default=str)
            result = self.client.setex(key, ttl, serialized)

            logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
            return bool(result)

        except Exception as e:
            logger.warning(f"Failed to set cache key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)

            if value:
                # Record cache hit
                self.metrics.put_metric(
                    "CacheHitRate",
                    1.0,
                    "Count",
                    {"Status": "hit"},
                )
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                # Record cache miss
                self.metrics.put_metric(
                    "CacheHitRate",
                    0.0,
                    "Count",
                    {"Status": "miss"},
                )
                logger.debug(f"Cache miss: {key}")
                return None

        except Exception as e:
            logger.warning(f"Failed to get cache key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.client:
            return False

        try:
            result = self.client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return bool(result)

        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
            return False

    def cache_topology(
        self,
        region: str,
        vpc_id: str,
        topology_data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache topology data.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            topology_data: Topology data
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        key = f"topology:{region}:{vpc_id}:latest"
        return self.set(key, topology_data, ttl)

    def get_cached_topology(
        self,
        region: str,
        vpc_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached topology data.

        Args:
            region: AWS region
            vpc_id: VPC identifier

        Returns:
            Cached topology or None
        """
        key = f"topology:{region}:{vpc_id}:latest"
        return self.get(key)

    def invalidate_topology(
        self,
        region: str,
        vpc_id: str,
    ) -> bool:
        """
        Invalidate cached topology.

        Args:
            region: AWS region
            vpc_id: VPC identifier

        Returns:
            True if invalidated
        """
        key = f"topology:{region}:{vpc_id}:latest"
        return self.delete(key)

    def clear_all(self) -> bool:
        """
        Clear all cached data (use with caution).

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("Cleared all cache data")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.client:
            return {"enabled": False}

        try:
            info = self.client.info()

            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
