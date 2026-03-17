import React from 'react';
import Header from './Header';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

/**
 * 主聊天窗口组件
 */
export default function ChatWindow({
  messages,
  isLoading,
  currentThoughts,
  currentSources,
  onSendMessage,
  onStopGeneration,
  useRag,
  setUseRag,
  useWebSearch,
  setUseWebSearch,
  isConnected,
}) {
  // 发送消息时传递选项
  const handleSendMessage = (content) => {
    onSendMessage(content, { useRag, useWebSearch });
  };

  return (
    <div className="flex-1 flex flex-col bg-dark-bg h-full">
      {/* 顶部导航 */}
      <Header
        useRag={useRag}
        setUseRag={setUseRag}
        useWebSearch={useWebSearch}
        setUseWebSearch={setUseWebSearch}
        isConnected={isConnected}
      />

      {/* 消息列表 */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        currentThoughts={currentThoughts}
        currentSources={currentSources}
      />

      {/* 输入框 */}
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onStopGeneration={onStopGeneration}
      />
    </div>
  );
}
