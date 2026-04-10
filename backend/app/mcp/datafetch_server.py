"""
Data Fetching Server - 为知识生成和RAG提供结构化的数据检索
"""

import logging
import json
from uuid import UUID
from typing import Optional

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.models.resource_chunk import ResourceChunk
from app.models.knowledge_node import KnowledgeNode
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.user import User
from app.mcp.base_server import BaseMCPServer

logger = logging.getLogger("certimate.mcp.datafetch")


class DataFetchServer(BaseMCPServer):
    """Data Fetching Server - 提供结构化数据检索"""

    def _register_functions(self) -> None:
        """注册 Data Fetching Server 的所有函数"""
        self._register("FetchContextForGeneration", self.fetch_context_for_generation)
        self._register("ExtractKnowledgeNodes", self.extract_knowledge_nodes)
        self._register("BatchFetchUserData", self.batch_fetch_user_data)
        self._register("SummarizeChatHistory", self.summarize_chat_history)
        self._register("GetRelationshipGraph", self.get_relationship_graph)

    async def fetch_context_for_generation(
        self,
        document_id: str,
        topic: str,
        max_chunks: int = 5
    ) -> dict:
        """
        为知识生成获取相关的文档块（用于RAG）

        参数:
            document_id: 资源文档 UUID
            topic: 知识主题名称
            max_chunks: 返回最多的块数量

        返回:
            {
                "chunks": [
                    {
                        "index": int,
                        "text": str,
                        "source_page": int,
                        "source_section": str
                    }
                ],
                "document_id": str,
                "total_chunks": int
            }
        """
        try:
            doc_uuid = UUID(document_id)

            # 获取文档
            document = self.db.query(Resource).filter_by(id=doc_uuid).first()
            if not document:
                return self.error(f"Document not found: {document_id}")

            # 获取相关的资源块（与主题相关）
            chunks = (
                self.db.query(ResourceChunk)
                .filter(ResourceChunk.resource_id == doc_uuid)
                .order_by(ResourceChunk.chunk_index.asc())
                .limit(max_chunks)
                .all()
            )

            chunks_data = []
            for chunk in chunks:
                chunks_data.append({
                    "index": chunk.chunk_index,
                    "text": chunk.text,
                    "source_page": chunk.page_number,
                    "source_section": chunk.section_header,
                })

            return self.success(
                data={
                    "chunks": chunks_data,
                    "document_id": document_id,
                    "total_chunks": len(chunks_data),
                }
            )
        except ValueError as e:
            return self.error(f"Invalid document_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching context: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def extract_knowledge_nodes(
        self,
        document_text: str,
        taxonomy: str = "bloom"
    ) -> dict:
        """
        从文档文本中提取结构化的知识节点

        参数:
            document_text: 文档内容
            taxonomy: 分类系统 ("bloom" 或 "custom")

        返回:
            {
                "nodes": [
                    {
                        "concept": str,
                        "definition": str,
                        "examples": [str],
                        "bloom_level": int,
                        "prerequisites": [str]
                    }
                ],
                "total_nodes": int
            }
        """
        try:
            # 简化版本：将文本分段作为节点
            # 实际应用中应该使用NLP或ML模型进行复杂提取

            if not document_text or len(document_text) == 0:
                return self.error("Document text is empty")

            # 按段落分割
            paragraphs = document_text.split('\n\n')
            nodes = []

            for i, para in enumerate(paragraphs[:10]):  # 限制为10个节点
                if len(para.strip()) < 20:
                    continue

                # 简单的节点构造
                lines = para.strip().split('\n')
                concept = lines[0].strip()[:100]  # 第一行作为概念

                node = {
                    "concept": concept,
                    "definition": '\n'.join(lines[1:3]) if len(lines) > 1 else para[:200],
                    "examples": [],  # 实际应用中应该提取示例
                    "bloom_level": self._estimate_bloom_level(para),
                    "prerequisites": [],  # 实际应该从知识图分析
                }
                nodes.append(node)

            return self.success(
                data={
                    "nodes": nodes,
                    "total_nodes": len(nodes),
                }
            )
        except Exception as e:
            logger.error(f"Error extracting knowledge nodes: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def batch_fetch_user_data(
        self,
        user_ids: list[str],
        fields: list[str] = None
    ) -> dict:
        """
        高效批量获取多个用户的数据

        参数:
            user_ids: 用户 UUID 列表
            fields: 要获取的字段列表 ["email", "display_name", "subscription_plan"]

        返回:
            {
                "users": [
                    {
                        "user_id": str,
                        "email": str,
                        "display_name": str,
                        ...
                    }
                ],
                "total_users": int
            }
        """
        try:
            if not user_ids:
                return self.error("user_ids list is empty")

            # 转换为 UUID 对象
            user_uuids = []
            for uid in user_ids:
                try:
                    user_uuids.append(UUID(uid))
                except ValueError:
                    logger.warning(f"Invalid UUID format: {uid}")
                    continue

            # 批量查询用户
            users = self.db.query(User).filter(User.id.in_(user_uuids)).all()

            # 构建返回数据
            default_fields = ["email", "display_name", "subscription_plan"]
            fields = fields or default_fields

            users_data = []
            for user in users:
                user_dict = {"user_id": str(user.id)}
                for field in fields:
                    if hasattr(user, field):
                        user_dict[field] = getattr(user, field)
                users_data.append(user_dict)

            return self.success(
                data={
                    "users": users_data,
                    "total_users": len(users_data),
                }
            )
        except Exception as e:
            logger.error(f"Error batch fetching user data: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def summarize_chat_history(
        self,
        session_id: str,
        window: int = 20
    ) -> dict:
        """
        压缩聊天历史，保留上下文的同时减少数据量

        参数:
            session_id: 聊天会话 UUID
            window: 保留的最后 N 条消息数量

        返回:
            {
                "session_id": str,
                "summary": str,
                "recent_messages": [
                    {
                        "role": str,
                        "content": str,
                        "timestamp": str
                    }
                ],
                "total_messages": int
            }
        """
        try:
            session_uuid = UUID(session_id)

            # 获取聊天会话
            session = self.db.query(AiChatSession).filter_by(id=session_uuid).first()
            if not session:
                return self.error(f"Chat session not found: {session_id}")

            # 获取最近的消息
            messages = (
                self.db.query(AiChatMessage)
                .filter(AiChatMessage.session_id == session_uuid)
                .order_by(desc(AiChatMessage.created_at))
                .limit(window)
                .all()
            )

            # 反向排序为正确的时间顺序
            messages.reverse()

            # 构建消息列表
            recent_messages = []
            for msg in messages:
                recent_messages.append({
                    "role": msg.role or "user",
                    "content": msg.content[:500],  # 限制长度
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                })

            # 简单的总结（实际应该使用LLM）
            total_messages = self.db.query(func.count(AiChatMessage.id)).filter(
                AiChatMessage.session_id == session_uuid
            ).scalar() or 0

            summary = f"Chat session with {total_messages} total messages. Recent {len(messages)} messages preserved."

            return self.success(
                data={
                    "session_id": session_id,
                    "summary": summary,
                    "recent_messages": recent_messages,
                    "total_messages": total_messages,
                }
            )
        except ValueError as e:
            return self.error(f"Invalid session_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error summarizing chat history: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def get_relationship_graph(
        self,
        concept_id: str
    ) -> dict:
        """
        获取特定概念的知识关系图

        参数:
            concept_id: 知识节点 UUID

        返回:
            {
                "concept_id": str,
                "concept_name": str,
                "prerequisites": [
                    {"concept_id": str, "concept_name": str}
                ],
                "reinforcements": [
                    {"concept_id": str, "concept_name": str}
                ]
            }
        """
        try:
            node_uuid = UUID(concept_id)

            # 获取节点
            node = self.db.query(KnowledgeNode).filter_by(id=node_uuid).first()
            if not node:
                return self.error(f"Knowledge node not found: {concept_id}")

            # 获取前置知识（父节点）
            prerequisites = []
            parent = node
            for _ in range(3):  # 限制深度为3
                if parent.parent_id:
                    parent = self.db.query(KnowledgeNode).filter_by(id=parent.parent_id).first()
                    if parent:
                        prerequisites.append({
                            "concept_id": str(parent.id),
                            "concept_name": parent.name,
                        })
                else:
                    break

            # 获取强化知识（子节点）
            children = self.db.query(KnowledgeNode).filter_by(parent_id=node_uuid).all()
            reinforcements = [
                {
                    "concept_id": str(child.id),
                    "concept_name": child.name,
                }
                for child in children[:5]  # 限制为5个子节点
            ]

            return self.success(
                data={
                    "concept_id": concept_id,
                    "concept_name": node.name,
                    "prerequisites": prerequisites,
                    "reinforcements": reinforcements,
                }
            )
        except ValueError as e:
            return self.error(f"Invalid concept_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting relationship graph: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    # === Helper Methods ===

    def _estimate_bloom_level(self, text: str) -> int:
        """
        简单地估计Bloom分类学级别（1-6）
        实际应用中应使用ML模型

        规则:
        - 定义性内容 → 1-2 (记住/理解)
        - 应用示例 → 3-4 (应用/分析)
        - 比较/评估 → 5-6 (评估/创建)
        """
        text_lower = text.lower()

        # 创建性词语
        if any(word in text_lower for word in ["design", "create", "develop", "invent"]):
            return 6

        # 评估词语
        if any(word in text_lower for word in ["evaluate", "justify", "critique", "compare"]):
            return 5

        # 分析词语
        if any(word in text_lower for word in ["analyze", "distinguish", "differentiate"]):
            return 4

        # 应用词语
        if any(word in text_lower for word in ["apply", "use", "implement", "solve"]):
            return 3

        # 理解词语
        if any(word in text_lower for word in ["explain", "describe", "summarize"]):
            return 2

        # 默认记住级别
        return 1
