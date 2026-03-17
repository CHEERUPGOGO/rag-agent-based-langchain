"""
对话检查点管理器 - 异步版本
使用 AsyncSqliteSaver 实现异步对话消息持久化
"""

import logging
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

logger = logging.getLogger(__name__)


class CheckpointManager:
    """管理 LangGraph 的对话状态和元数据（异步版本）"""

    def __init__(self, db_path: str = "checkpoint.db"):
        """
        初始化检查点管理器
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._initialized = False
        logger.info(f"CheckpointManager initialized with db: {db_path}")

    async def _ensure_db_exists(self):
        """确保数据库存在并创建必要的表"""
        if self._initialized:
            return
            
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as conn:
            # 创建对话表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    metadata_json TEXT
                )
            """)
            
            # 创建消息表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            
            # 创建索引加速查询
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_id 
                ON conversation_messages(conversation_id)
            """)
            
            await conn.commit()
            self._initialized = True
            logger.debug("Database tables initialized")

    async def create_conversation(
        self, 
        conversation_id: str, 
        user_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> None:
        """创建新对话记录"""
        await self._ensure_db_exists()
        now = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT OR IGNORE INTO conversations 
                (id, user_id, title, created_at, updated_at, message_count, status)
                VALUES (?, ?, ?, ?, ?, 0, 'active')
            """, (conversation_id, user_id, title or "新对话", now, now))
            await conn.commit()
        
        logger.debug(f"Conversation created: {conversation_id}")

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None
    ) -> None:
        """添加消息记录"""
        now = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as conn:
            # 确保对话存在并获取当前标题
            cursor = await conn.execute(
                "SELECT id, title, user_id FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = await cursor.fetchone()
            
            current_title = None
            current_user_id = None
            if not row:
                await self.create_conversation(conversation_id, user_id=user_id)
                current_title = "新对话"
            else:
                current_title = row[1]
                current_user_id = row[2]
                if user_id and not current_user_id:
                    await conn.execute(
                        "UPDATE conversations SET user_id = ? WHERE id = ?",
                        (user_id, conversation_id),
                    )
            
            # 添加消息
            await conn.execute("""
                INSERT INTO conversation_messages 
                (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, role, content, now))
            
            # 检查是否需要更新标题
            new_title = None
            if role == "user" and (current_title == "新对话" or current_title is None):
                clean_content = content.strip()
                if clean_content:
                    # 取第一行前30个字符作为标题
                    first_line = clean_content.split('\n')[0]
                    new_title = first_line[:30]
                    if len(first_line) > 30:
                        new_title += "..."
            
            # 更新消息计数和标题（如果需要）
            if new_title:
                await conn.execute("""
                    UPDATE conversations 
                    SET updated_at = ?, message_count = message_count + 1, title = ?
                    WHERE id = ?
                """, (now, new_title, conversation_id))
            else:
                await conn.execute("""
                    UPDATE conversations 
                    SET updated_at = ?, message_count = message_count + 1
                    WHERE id = ?
                """, (now, conversation_id))
            
            await conn.commit()
        
        logger.debug(f"Message added to {conversation_id}")

    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话的消息历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("""
                    SELECT role, content, created_at FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                """, (conversation_id,))
                
                rows = await cursor.fetchall()
                messages = []
                for row in rows:
                    messages.append({
                        "role": row[0],
                        "content": row[1],
                        "timestamp": row[2]
                    })
                
                return messages
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话的完整 checkpoint 状态"""
        try:
            async with AsyncSqliteSaver.from_conn_string(self.db_path) as saver:
                config = {"configurable": {"thread_id": conversation_id}}
                state = await saver.aget_state(config)
                if state:
                    return {
                        "values": state.values,
                        "metadata": state.metadata,
                        "checkpoint": state.checkpoint
                    }
        except Exception as e:
            logger.warning(f"Failed to get checkpoint state: {e}")
        
        return None

    async def get_all_checkpoints(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话的所有版本/检查点"""
        checkpoints = []
        
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("""
                    SELECT checkpoint_id, parent_checkpoint_id, type_name
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY checkpoint_id DESC
                    LIMIT 10
                """, (conversation_id,))
                
                rows = await cursor.fetchall()
                for row in rows:
                    checkpoints.append({
                        "checkpoint_id": row[0],
                        "parent_checkpoint_id": row[1],
                        "type_name": row[2]
                    })
        except Exception as e:
            logger.error(f"Error getting checkpoints: {e}")
        
        return checkpoints

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """列出对话列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                if user_id:
                    cursor = await conn.execute("""
                        SELECT id, title, created_at, updated_at, message_count
                        FROM conversations
                        WHERE status = 'active' AND user_id = ?
                        ORDER BY updated_at DESC
                        LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor = await conn.execute("""
                        SELECT id, title, created_at, updated_at, message_count
                        FROM conversations
                        WHERE status = 'active'
                        ORDER BY updated_at DESC
                        LIMIT ?
                    """, (limit,))
                
                rows = await cursor.fetchall()
                conversations = []
                for row in rows:
                    conversations.append({
                        "id": row[0],
                        "title": row[1],
                        "created_at": row[2],
                        "updated_at": row[3],
                        "message_count": row[4]
                    })
                
                return conversations
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> None:
        """删除对话（软删除）"""
        now = datetime.now().isoformat()
        
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                    UPDATE conversations 
                    SET status = 'deleted', updated_at = ?
                    WHERE id = ?
                """, (now, conversation_id))
                await conn.commit()
            
            logger.debug(f"Conversation deleted: {conversation_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise


# 全局单例实例
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager(db_path: str = "checkpoint.db") -> CheckpointManager:
    """获取全局检查点管理器实例"""
    global _checkpoint_manager
    
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(db_path)
    
    return _checkpoint_manager
