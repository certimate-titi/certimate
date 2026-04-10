"""Base MCP Server class with common functionality."""

import time
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps
from sqlalchemy.orm import Session

from app.mcp.types import MCPResponse, MCPErrorType, error_response, success_response

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base class for all MCP servers providing common functionality."""

    def __init__(self, db: Session, enable_caching: bool = True):
        """
        Initialize MCP server.

        Args:
            db: SQLAlchemy session for database access
            enable_caching: Whether to enable function-level caching
        """
        self.db = db
        self.enable_caching = enable_caching
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self.name = self.__class__.__name__

    def log_function_call(self, function_name: str, user_id: Optional[str] = None, **kwargs) -> None:
        """Log an MCP function call for observability."""
        logger.info(
            f"MCP[{self.name}].{function_name} called",
            extra={
                "mcp_server": self.name,
                "mcp_function": function_name,
                "user_id": user_id,
                "params": str(kwargs)[:200]  # Truncate for logging
            }
        )

    def log_function_result(
        self,
        function_name: str,
        elapsed_ms: float,
        success: bool,
        user_id: Optional[str] = None
    ) -> None:
        """Log MCP function result for observability."""
        logger.info(
            f"MCP[{self.name}].{function_name} completed",
            extra={
                "mcp_server": self.name,
                "mcp_function": function_name,
                "user_id": user_id,
                "elapsed_ms": elapsed_ms,
                "success": success
            }
        )

    def with_observability(self, function_name: str):
        """Decorator for adding observability to MCP functions."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                user_id = kwargs.get("user_id")

                try:
                    self.log_function_call(function_name, user_id=user_id, **kwargs)
                    result = func(*args, **kwargs)
                    elapsed_ms = (time.time() - start_time) * 1000
                    self.log_function_result(function_name, elapsed_ms, True, user_id=user_id)
                    return result
                except Exception as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    self.log_function_result(function_name, elapsed_ms, False, user_id=user_id)
                    logger.error(
                        f"MCP[{self.name}].{function_name} error: {str(e)}",
                        exc_info=True
                    )
                    raise

            return wrapper
        return decorator

    def with_caching(self, ttl_seconds: int = 300):
        """
        Decorator for adding caching to MCP functions.

        Cache key is generated from function name + all kwargs.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self.enable_caching:
                    return func(*args, **kwargs)

                # Generate cache key
                cache_key = f"{func.__name__}:{str(kwargs)}"

                # Check cache
                if cache_key in self._cache:
                    cache_time = self._cache_timestamps.get(cache_key, 0)
                    if time.time() - cache_time < ttl_seconds:
                        logger.debug(f"Cache HIT: {cache_key}")
                        return self._cache[cache_key]
                    else:
                        # Expired
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]

                # Cache miss - call function
                result = func(*args, **kwargs)
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
                logger.debug(f"Cache MISS: {cache_key} (ttl={ttl_seconds}s)")
                return result

            return wrapper
        return decorator

    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Optional regex pattern to match keys. If None, clears all.

        Returns:
            Number of entries cleared.
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            return count

        import re
        compiled_pattern = re.compile(pattern)
        keys_to_delete = [k for k in self._cache.keys() if compiled_pattern.match(k)]
        count = len(keys_to_delete)

        for key in keys_to_delete:
            del self._cache[key]
            del self._cache_timestamps[key]

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for ts in self._cache_timestamps.values()
            if time.time() - ts > 3600  # Count entries older than 1 hour
        )
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "cache_size_approx_kb": sum(
                len(str(v)) for v in self._cache.values()
            ) / 1024
        }

    def ok(self, data: Any = None) -> MCPResponse:
        """Create a success response."""
        return success_response(data)

    def error(
        self,
        message: str,
        error_type: MCPErrorType = MCPErrorType.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """Create an error response."""
        return error_response(error_type, message, details)

    def close(self) -> None:
        """Cleanup and close the server."""
        self.db.close()
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info(f"MCP[{self.name}] closed")


class MCPServerFactory:
    """Factory for creating MCP server instances with dependency injection."""

    _servers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, server_class: type) -> None:
        """Register an MCP server class."""
        cls._servers[name] = server_class
        logger.info(f"Registered MCP server: {name}")

    @classmethod
    def create(cls, name: str, db: Session, enable_caching: bool = True) -> BaseMCPServer:
        """
        Create an MCP server instance.

        Args:
            name: Server name (must be registered)
            db: SQLAlchemy session
            enable_caching: Whether to enable caching

        Returns:
            MCP server instance

        Raises:
            ValueError: If server name not registered
        """
        if name not in cls._servers:
            raise ValueError(f"Unknown MCP server: {name}. Registered: {list(cls._servers.keys())}")

        server_class = cls._servers[name]
        return server_class(db, enable_caching=enable_caching)

    @classmethod
    def get_registered_servers(cls) -> Dict[str, type]:
        """Get all registered servers."""
        return cls._servers.copy()
