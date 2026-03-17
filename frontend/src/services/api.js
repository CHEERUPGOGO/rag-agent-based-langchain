/**
 * API 服务模块
 * 处理与后端的所有通信
 */

const API_BASE_URL = '/api';

function buildErrorMessage(prefix, status, errorText = '') {
  let errorMessage = `${prefix}: ${status}`;

  if (errorText.includes('Authentication') || errorText.includes('governor')) {
    return 'API认证失败，请检查API密钥配置';
  }

  if (errorText) {
    errorMessage += ` - ${errorText}`;
  }

  return errorMessage;
}

async function ensureOk(response, prefix) {
  if (response.ok) {
    return response;
  }

  const errorText = await response.text();
  throw new Error(buildErrorMessage(prefix, response.status, errorText));
}

function parseSseBlock(block) {
  const lines = block.split('\n');
  let eventType = 'message';
  const dataLines = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(':')) {
      continue;
    }
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
      continue;
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  const payload = dataLines.join('\n');
  const parsed = JSON.parse(payload);
  if (!parsed.type && eventType) {
    parsed.type = eventType;
  }
  return parsed;
}

/**
 * 发送聊天消息（非流式）
 */
export async function sendMessage(message, options = {}) {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: options.conversationId,
      user_id: options.userId,
      history: options.history || [],
      use_rag: options.useRag !== false,
      use_web_search: options.useWebSearch !== false,
      stream: false,
    }),
  });

  await ensureOk(response, 'API error');
  return response.json();
}

/**
 * 发送聊天消息（流式）
 */
export async function* sendMessageStream(message, options = {}) {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    signal: options.signal,
    body: JSON.stringify({
      message,
      conversation_id: options.conversationId,
      user_id: options.userId,
      history: options.history || [],
      use_rag: options.useRag !== false,
      use_web_search: options.useWebSearch !== false,
      stream: true,
    }),
  });

  await ensureOk(response, 'API error');

  if (!response.body) {
    throw new Error('Streaming response body is empty');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || '';

    for (const block of blocks) {
      if (!block.trim()) {
        continue;
      }
      const parsed = parseSseBlock(block);
      if (parsed) {
        yield parsed;
      }
    }
  }

  if (buffer.trim()) {
    const parsed = parseSseBlock(buffer);
    if (parsed) {
      yield parsed;
    }
  }
}

/**
 * 上传文档
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  await ensureOk(response, 'Upload failed');
  return response.json();
}

/**
 * 批量上传文档
 */
export async function uploadDocumentsBatch(files) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}/documents/upload/batch`, {
    method: 'POST',
    body: formData,
  });

  await ensureOk(response, 'Batch upload failed');
  return response.json();
}

/**
 * 获取文档列表
 */
export async function getDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents/`);
  await ensureOk(response, 'Failed to get documents');
  return response.json();
}

/**
 * 删除文档
 */
export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  });

  await ensureOk(response, 'Failed to delete document');
  return response.json();
}

/**
 * 获取知识库统计信息
 */
export async function getDocumentStats() {
  const response = await fetch(`${API_BASE_URL}/documents/stats/overview`);
  await ensureOk(response, 'Failed to get stats');
  return response.json();
}

/**
 * 评估RAG效果
 */
export async function evaluateRAG(samples, metrics = null) {
  const response = await fetch(`${API_BASE_URL}/evaluation/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      samples,
      metrics,
    }),
  });

  await ensureOk(response, 'Evaluation failed');
  return response.json();
}

/**
 * 获取可用评估指标
 */
export async function getEvaluationMetrics() {
  const response = await fetch(`${API_BASE_URL}/evaluation/metrics`);
  await ensureOk(response, 'Failed to get metrics');
  return response.json();
}

/**
 * 获取对话列表
 */
export async function getConversations(limit = 20, userId = null) {
  let url = `${API_BASE_URL}/chat/conversations?limit=${limit}`;
  if (userId) {
    url += `&user_id=${userId}`;
  }
  const response = await fetch(url);
  await ensureOk(response, 'Failed to get conversations');
  return response.json();
}

/**
 * 获取对话历史记录
 */
export async function getConversationHistory(conversationId, userId) {
  const url = new URL(`${API_BASE_URL}/chat/conversations/${conversationId}/history`, window.location.origin);
  if (userId) url.searchParams.append('user_id', userId);
  const response = await fetch(url.toString());
  await ensureOk(response, 'Failed to get conversation history');
  return response.json();
}

/**
 * 获取对话完整状态
 */
export async function getConversationState(conversationId, userId) {
  const url = new URL(`${API_BASE_URL}/chat/conversations/${conversationId}/state`, window.location.origin);
  if (userId) url.searchParams.append('user_id', userId);
  const response = await fetch(url.toString());
  await ensureOk(response, 'Failed to get conversation state');
  return response.json();
}

/**
 * 删除对话
 */
export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
  await ensureOk(response, 'Failed to delete conversation');
  return response.json();
}

/**
 * 健康检查
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.ok;
}

/**
 * 获取配置信息
 */
export async function getConfig() {
  const response = await fetch(`${API_BASE_URL}/config`);
  await ensureOk(response, 'Failed to get config');
  return response.json();
}
