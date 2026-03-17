import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import DocumentModal from './components/DocumentModal';
import EvaluationPanel from './components/EvaluationPanel';
import { useChat } from './hooks/useChat';
import { healthCheck, getConversations, deleteConversation } from './services/api';

/**
 * 主应用组件
 */
export default function App() {
  // 聊天状态
  const {
    messages,
    isLoading,
    isLoadingHistory,
    error,
    conversationId,
    currentThoughts,
    currentSources,
    sendMessage,
    stopGeneration,
    clearMessages,
    loadConversationHistory,
    userId,
  } = useChat();

  // UI状态
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [useRag, setUseRag] = useState(true);
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [isConnected, setIsConnected] = useState(true);
  const [showDocuments, setShowDocuments] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showEvaluation, setShowEvaluation] = useState(false);

  // 对话列表 - 从后端加载
  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);

  // 加载对话列表
  const loadConversations = async () => {
    setIsLoadingConversations(true);
    try {
      const data = await getConversations(50, userId);
      if (data.conversations) {
        setConversations(data.conversations);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  // 健康检查
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const healthy = await healthCheck();
        setIsConnected(healthy);
      } catch {
        setIsConnected(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // 应用启动时加载对话列表
  useEffect(() => {
    if (userId) {
      loadConversations();
    }
  }, [userId]);

  // 当有新消息时，刷新对话列表（更新最近访问时间）
  useEffect(() => {
    if (messages.length > 0) {
      // 延迟加载以避免频繁刷新
      const timer = setTimeout(() => {
        loadConversations();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [messages]);

  // 新建对话
  const handleNewChat = () => {
    clearMessages();
    // 新对话将由 useChat 生成新的 conversation_id
  };

  // 选择已有对话
  const handleSelectConversation = async (conversationId) => {
    await loadConversationHistory(conversationId);
  };

  // 删除对话
  const handleDeleteConversation = async (deletedConversationId) => {
    if (!window.confirm('确定要删除这个对话吗？')) {
      return;
    }
    try {
      await deleteConversation(deletedConversationId);
      // 重新加载对话列表
      await loadConversations();
      // 如果删除的是当前对话，清空消息
      if (deletedConversationId === conversationId) {
        clearMessages();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  return (
    <div className="h-screen flex overflow-hidden">
      {/* 侧边栏 */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={handleNewChat}
        onClearChat={clearMessages}
        conversations={conversations}
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        isLoadingConversations={isLoadingConversations}
        onOpenDocuments={() => setShowDocuments(true)}
        onOpenSettings={() => setShowSettings(true)}
        onOpenEvaluation={() => setShowEvaluation(true)}
      />

      {/* 主聊天区域 */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading || isLoadingHistory}
        currentThoughts={currentThoughts}
        currentSources={currentSources}
        onSendMessage={sendMessage}
        onStopGeneration={stopGeneration}
        useRag={useRag}
        setUseRag={setUseRag}
        useWebSearch={useWebSearch}
        setUseWebSearch={setUseWebSearch}
        isConnected={isConnected}
      />

      {/* 文档管理弹窗 */}
      <DocumentModal
        isOpen={showDocuments}
        onClose={() => setShowDocuments(false)}
      />

      {/* RAG 评估面板 */}
      <EvaluationPanel
        isOpen={showEvaluation}
        onClose={() => setShowEvaluation(false)}
      />

      {/* 错误提示 */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}
