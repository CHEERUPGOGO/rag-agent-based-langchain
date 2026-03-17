# 项目计划：通过 LangGraph 中的 AsyncSqliteSaver 实现对话持久化

本计划旨在通过 `langgraph-checkpoint-sqlite` 中的 `AsyncSqliteSaver` 为项目实现对话历史的持久化存储。这将确保即使服务重启，对话历史仍能从 SQLite 数据库中恢复。

## 目标
- 集成 `AsyncSqliteSaver` 作为 LangGraph 的 Checkpointer。
- 实现对话状态的自动保存与加载。
- 确保对话历史跨服务重启持久存在。
- 优化代码逻辑，减少手动历史管理，利用 LangGraph 的内置持久化机制。

## 实施步骤

### 1. 更新依赖
- 在 `backend/requirements.txt` 中添加 `langgraph-checkpoint-sqlite`。

### 2. 重构 Agent 执行器 (`backend/app/agent/agent.py`)
- **修正导入**：
  - 将 `from langchain.agents import create_agent` 修改为 `from langgraph.prebuilt import create_react_agent`。
  - 确保 `AsyncSqliteSaver` 的导入路径正确。
- **重写 `chat` 和 `stream_chat` 方法**：
  - 使用 `AsyncSqliteSaver.from_conn_string(settings.checkpoint_db_path)` 作为异步上下文管理器。
  - 在上下文管理器内部创建 `create_react_agent` 实例并传入 `checkpointer`。
  - 调用 `ainvoke` 或 `astream_events` 时，传入 `config={"configurable": {"thread_id": conversation_id}}`。
  - 优化消息处理逻辑：
    - 如果是已有对话，利用 Checkpointer 自动加载历史。
    - 如果是新对话，初始化系统提示词。
- **更新事件处理**：
  - 确保流式输出能正确捕获 `on_chat_model_stream`、`on_tool_start` 和 `on_tool_end` 事件。

### 3. 完善检查点管理器 (`backend/app/conversation/checkpoint_manager.py`)
- **异步支持**：
  - 确保 `CheckpointManager` 中的 `get_conversation_state` 等方法能正确处理 `AsyncSqliteSaver` 的异步调用。
- **清理逻辑**：
  - 移除或简化与 `AsyncSqliteSaver` 功能重叠的手动消息保存逻辑（如果适用）。

### 4. 验证与测试
- 启动后端服务。
- 发起一段对话，记录 `conversation_id`。
- 重启后端服务。
- 通过 `/api/chat/conversations/{conversation_id}/history` 验证历史记录是否仍然存在。
- 继续之前的对话，验证 Agent 是否记得之前的上下文。

## 预期结果
- 成功在 `./checkpoint.db` 中生成 LangGraph 的 checkpointer 表。
- 对话历史能够根据 `thread_id` 自动保存和恢复。
- 系统架构更加符合 LangGraph 的最佳实践。
