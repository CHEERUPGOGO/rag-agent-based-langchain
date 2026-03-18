# LangChain RAG Agent

基于LangChain 1.0的全栈式Agent交流平台，支持RAG检索和联网搜索功能。

## 项目结构

```
backend/          # 后端服务
├── app/          # 应用代码
│   ├── agent/    # Agent核心逻辑
│   ├── rag/      # RAG检索模块
│   ├── routers/  # API路由
│   └── models/   # 数据模型
├── run.py        # 启动脚本
└── requirements.txt # 依赖列表

frontend/         # 前端代码
```

## 功能特性

- 基于LangGraph的智能Agent
- RAG文档检索功能 完整的文档生态管理
- 联网搜索功能
- 流式对话响应
- 支持多种大语言模型

## 环境配置

在 `backend/.env` 文件中配置以下环境变量：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Tavily搜索API
TAVILY_API_KEY=your_tavily_api_key

# Ollama配置（可选）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
```

## 启动项目

### 后端服务

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端服务将启动在 `http://localhost:8000`

### 前端服务

```bash
cd frontend
npm install
npm run dev
```

前端服务将启动在 `http://localhost:5173`