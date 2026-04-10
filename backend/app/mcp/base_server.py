"""
MCP 服务器基类 - 提供通用的服务器框架
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.mcp.types import MCPRequest, MCPResponse

logger = logging.getLogger("certimate.mcp")


class BaseMCPServer(ABC):
    """MCP 服务器基类"""

    def __init__(self, db: Session):
        self.db = db
        self._functions: dict[str, Callable] = {}
        self._register_functions()

    def _register_functions(self) -> None:
        """注册所有 MCP 函数（由子类实现）"""
        pass

    def _register(self, name: str, func: Callable) -> None:
        """注册一个 MCP 函数"""
        self._functions[name] = func
        logger.debug(f"Registered MCP function: {name}")

    async def call(self, request: MCPRequest) -> MCPResponse:
        """调用 MCP 函数"""
        try:
            if request.function not in self._functions:
                return MCPResponse(
                    status="error",
                    error=f"Unknown function: {request.function}",
                )

            func = self._functions[request.function]
            result = await func(**request.params) if hasattr(func, "__await__") else func(**request.params)

            return MCPResponse(
                status="success",
                data=result,
            )
        except ValueError as e:
            return MCPResponse(
                status="error",
                error=f"Invalid parameters: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error calling {request.function}: {str(e)}", exc_info=True)
            return MCPResponse(
                status="error",
                error=f"Internal server error: {str(e)}",
            )

    def success(self, data: Any = None, **kwargs) -> dict:
        """生成成功响应"""
        return {"error": False, "data": data, **kwargs}

    def error(self, message: str, status_code: int = 400, **kwargs) -> dict:
        """生成错误响应"""
        return {"error": True, "message": message, "status_code": status_code, **kwargs}

    @abstractmethod
    async def _register_functions(self) -> None:
        """子类必须实现此方法来注册自己的函数"""
        pass


class MCPServerFactory:
    """MCP 服务器工厂 - 创建和管理 MCP 服务器实例"""

    _instances: dict[str, BaseMCPServer] = {}

    @classmethod
    def get_context_server(cls, db: Session) -> "BaseMCPServer":
        """获取 Context Server 实例（单例）"""
        key = "context_server"
        if key not in cls._instances:
            from app.mcp.context_server import ContextServer
            cls._instances[key] = ContextServer(db)
        return cls._instances[key]

    @classmethod
    def get_recommendation_server(cls, db: Session) -> "BaseMCPServer":
        """获取 Recommendation Server 实例（单例）"""
        key = "recommendation_server"
        if key not in cls._instances:
            from app.mcp.recommendation_server import RecommendationServer
            cls._instances[key] = RecommendationServer(db)
        return cls._instances[key]

    @classmethod
    def reset(cls) -> None:
        """重置所有实例（用于测试）"""
        cls._instances.clear()
